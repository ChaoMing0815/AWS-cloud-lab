import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
PUBLIC_NGINX = ROOT / "ops/nginx/co-story-public.conf"
BOOTSTRAP_NGINX = ROOT / "ops/nginx/co-story-public-bootstrap.conf"
PUBLIC_NGINX_UNIT = ROOT / "ops/systemd/co-story-nginx-public.service"
RENEW_UNIT = ROOT / "ops/systemd/co-story-certbot-renew.service"
RENEW_TIMER = ROOT / "ops/systemd/co-story-certbot-renew.timer"
ENABLE = ROOT / "ops/release/enable_public_https.sh"
DISABLE = ROOT / "ops/release/disable_public_https.sh"
RENEW = ROOT / "ops/release/renew_public_certificate.sh"


def _read(path: Path) -> str:
    assert path.is_file(), f"public HTTPS asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_public_nginx_serves_only_acme_over_http_and_proxies_https_to_loopback() -> None:
    config = _read(PUBLIC_NGINX)

    assert "listen 80 default_server;" in config
    assert "location ^~ /.well-known/acme-challenge/" in config
    assert "root /var/lib/co-story/acme;" in config
    assert "try_files $uri =404;" in config
    assert "server_name __PUBLIC_IP__;" in config
    assert "return 301 https://$server_name$request_uri;" in config
    assert "https://$host" not in config
    assert "listen 443 ssl default_server;" in config
    assert "include /etc/nginx/co-story-tls.conf;" in config
    assert "proxy_pass http://127.0.0.1:8000;" in config
    assert "proxy_set_header X-Forwarded-Proto https;" in config
    assert "0.0.0.0:8000" not in config
    assert "access_log off;" in config


def test_acme_bootstrap_never_exposes_the_application_over_plain_http() -> None:
    config = _read(BOOTSTRAP_NGINX)

    assert "listen 80 default_server;" in config
    assert "location ^~ /.well-known/acme-challenge/" in config
    assert "root /var/lib/co-story/acme;" in config
    assert "try_files $uri =404;" in config
    assert "location /" in config
    assert "return 404;" in config
    assert "listen 443" not in config
    assert "proxy_pass" not in config


def test_public_nginx_and_certificate_renewal_are_hardened_systemd_units() -> None:
    nginx_unit = _read(PUBLIC_NGINX_UNIT)
    renew_unit = _read(RENEW_UNIT)
    timer = _read(RENEW_TIMER)

    assert "Requires=co-story.service" in nginx_unit
    assert "ExecStartPre=/usr/sbin/nginx -t -c /etc/nginx/co-story-public.conf" in nginx_unit
    assert "ExecStart=/usr/sbin/nginx -e stderr -c /etc/nginx/co-story-public.conf" in nginx_unit
    assert "NoNewPrivileges=true" in nginx_unit
    assert "PrivateTmp=true" in nginx_unit
    assert "ProtectSystem=strict" in nginx_unit
    assert "ExecStart=/opt/co-story/current/ops/release/renew_public_certificate.sh" in renew_unit
    assert "OnUnitActiveSec=12h" in timer
    assert "RandomizedDelaySec=30m" in timer
    assert "Persistent=true" in timer


def test_public_https_enablement_is_pinned_bounded_and_fail_closed() -> None:
    script = _read(ENABLE)

    assert 'if [ "$(id -u)" -ne 0 ]; then' in script
    assert "validate_public_ipv4" in script
    assert 'certbot==5.4.0' in script
    assert "--preferred-profile shortlived" in script
    assert "--webroot" in script
    assert "--webroot-path /var/lib/co-story/acme" in script
    assert '--ip-address "$public_ip"' in script
    assert "--register-unsafely-without-email" in script
    assert "renew --dry-run --non-interactive" in script
    assert "openssl x509" in script
    assert "IP Address:$public_ip" in script
    assert "-checkend 86400" in script
    assert "ipaddress.ip_address" in script
    assert "address.is_global" in script
    assert "__PUBLIC_IP__" in script
    assert "CO_STORY_ENV=production" in script
    assert "CO_STORY_COOKIE_SECURE=true" in script
    assert 'CO_STORY_ALLOWED_HOSTS=$public_ip' in script
    assert 'CO_STORY_ALLOWED_ORIGINS=https://$public_ip' in script
    assert "amazon.nova-lite-v1:0" in script
    assert "CO_STORY_BEDROCK_GUARDRAIL_VERSION=1" in script
    assert "systemctl disable --now co-story-nginx-staging.service" in script
    assert "systemctl enable --now co-story-nginx-public.service" in script
    assert "systemctl enable --now co-story-certbot-renew.timer" in script
    assert "nginx -t -c /etc/nginx/co-story-public.conf" in script
    assert "set -x" not in script
    assert "aws " not in script
    assert "DATABASE_URL=" not in script


def test_public_https_rollback_restores_verified_internal_staging_before_cert_cleanup() -> None:
    script = _read(DISABLE)

    start_staging_at = script.index("systemctl enable --now co-story-nginx-staging.service")
    readiness_at = script.index("http://127.0.0.1:8080/api/v1/ready", start_staging_at)
    cert_cleanup_at = script.index("certbot delete", readiness_at)
    assert start_staging_at < readiness_at < cert_cleanup_at
    assert "CO_STORY_ENV=staging" in script
    assert "CO_STORY_COOKIE_SECURE=false" in script
    assert "systemctl disable --now co-story-certbot-renew.timer" in script
    assert "systemctl disable --now co-story-nginx-public.service" in script
    assert "readiness_attempts=30" in script
    assert "set -x" not in script
    assert "aws " not in script


def test_renewal_validates_nginx_before_reload_and_never_logs_secrets() -> None:
    script = _read(RENEW)

    renew_at = script.index("certbot renew")
    validate_at = script.index("nginx -t", renew_at)
    reload_at = script.index("systemctl reload co-story-nginx-public.service", validate_at)
    assert renew_at < validate_at < reload_at
    assert "set -x" not in script
    assert "DATABASE_URL" not in script
    assert "password" not in script.lower()


def test_public_https_shell_assets_have_valid_bash_syntax() -> None:
    for path in (ENABLE, DISABLE, RENEW):
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
