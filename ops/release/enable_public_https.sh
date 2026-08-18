#!/usr/bin/env bash
set -euo pipefail

validate_public_ipv4() {
  candidate="${1:?public IPv4 required}"
  case "$candidate" in
    *[!0-9.]* | .* | *. | *..*) return 1 ;;
  esac
  old_ifs="$IFS"
  IFS=.
  set -- $candidate
  IFS="$old_ifs"
  [ "$#" -eq 4 ] || return 1
  for octet in "$@"; do
    [ -n "$octet" ] || return 1
    [ "$octet" -ge 0 ] 2>/dev/null || return 1
    [ "$octet" -le 255 ] || return 1
  done
  python3.13 -c \
    'import ipaddress,sys; address=ipaddress.ip_address(sys.argv[1]); raise SystemExit(0 if address.version == 4 and address.is_global else 1)' \
    "$candidate"
}

render_nginx_config() {
  source_path="${1:?source config required}"
  destination_path="${2:?destination config required}"
  rendered_tmp="$(mktemp /etc/nginx/.co-story-public.conf.XXXXXX)"
  sed "s/__PUBLIC_IP__/$public_ip/g" "$source_path" > "$rendered_tmp"
  chmod 0644 "$rendered_tmp"
  mv -f "$rendered_tmp" "$destination_path"
}

wait_for_readiness() {
  readiness_url="${1:?readiness URL required}"
  readiness_host="${2:?readiness host required}"
  readiness_resolve="${3:?curl resolve required}"
  readiness_attempts=30
  readiness_attempt=1
  while [ "$readiness_attempt" -le "$readiness_attempts" ]; do
    if curl --fail --silent --max-time 2 \
      --resolve "$readiness_resolve" \
      --header "Host: $readiness_host" "$readiness_url" >/dev/null; then
      return 0
    fi
    if [ "$readiness_attempt" -lt "$readiness_attempts" ]; then
      sleep 1
    fi
    readiness_attempt=$((readiness_attempt + 1))
  done
  printf '%s\n' "readiness check failed: $readiness_url" >&2
  return 1
}

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'public HTTPS enablement must run as root' >&2
  exit 2
fi

public_ip="${1:?public IPv4 required}"
guardrail_id="${2:?Bedrock Guardrail ID required}"
if ! validate_public_ipv4 "$public_ip"; then
  printf '%s\n' 'invalid public IPv4' >&2
  exit 2
fi
case "$guardrail_id" in
  *[!a-z0-9]* | '') printf '%s\n' 'invalid Guardrail ID' >&2; exit 2 ;;
esac

root=/opt/co-story
active_release="$(readlink -f "$root/current" 2>/dev/null || true)"
resolved_releases="$(realpath -e "$root/releases")"
case "$active_release" in
  "$resolved_releases"/*) ;;
  *) printf '%s\n' 'invalid active release' >&2; exit 2 ;;
esac
test -d "$active_release"

state_dir=/var/lib/co-story/public-https
install -d -m 0700 "$state_dir"
if [ ! -f "$state_dir/runtime.env.before-public" ]; then
  install -m 0640 -o root -g co-story /etc/co-story/runtime.env \
    "$state_dir/runtime.env.before-public"
fi

success=0
restore_staging() {
  systemctl disable --now co-story-certbot-renew.timer >/dev/null 2>&1 || true
  systemctl disable --now co-story-nginx-public.service >/dev/null 2>&1 || true
  if [ -f "$state_dir/runtime.env.before-public" ]; then
    install -m 0640 -o root -g co-story "$state_dir/runtime.env.before-public" \
      /etc/co-story/runtime.env
  fi
  systemctl restart co-story.service || true
  systemctl enable --now co-story-nginx-staging.service >/dev/null 2>&1 || true
}
cleanup() {
  if [ "$success" -eq 0 ]; then
    restore_staging
  fi
}
trap cleanup EXIT

python3.13 -m venv "$root/certbot"
"$root/certbot/bin/python" -m pip install --disable-pip-version-check 'certbot==5.4.0'
case "$("$root/certbot/bin/certbot" --version)" in
  'certbot 5.4.0') ;;
  *) printf '%s\n' 'unexpected Certbot version' >&2; exit 2 ;;
esac

install -d -m 0755 -o root -g root /var/lib/co-story/acme
install -m 0644 "$active_release/ops/systemd/co-story-nginx-public.service" \
  /etc/systemd/system/co-story-nginx-public.service
install -m 0644 "$active_release/ops/systemd/co-story-certbot-renew.service" \
  /etc/systemd/system/co-story-certbot-renew.service
install -m 0644 "$active_release/ops/systemd/co-story-certbot-renew.timer" \
  /etc/systemd/system/co-story-certbot-renew.timer
render_nginx_config "$active_release/ops/nginx/co-story-public-bootstrap.conf" \
  /etc/nginx/co-story-public.conf
systemctl daemon-reload
systemctl disable --now co-story-nginx-staging.service
systemctl enable --now co-story-nginx-public.service

staging_root="$state_dir/letsencrypt-staging"
install -d -m 0700 "$staging_root/config" "$staging_root/work" "$staging_root/logs"
"$root/certbot/bin/certbot" certonly --staging --non-interactive --agree-tos \
  --register-unsafely-without-email --preferred-profile shortlived --webroot \
  --webroot-path /var/lib/co-story/acme --ip-address "$public_ip" \
  --config-dir "$staging_root/config" --work-dir "$staging_root/work" \
  --logs-dir "$staging_root/logs"
"$root/certbot/bin/certbot" certonly --non-interactive --agree-tos \
  --register-unsafely-without-email --preferred-profile shortlived --webroot \
  --webroot-path /var/lib/co-story/acme --ip-address "$public_ip"
"$root/certbot/bin/certbot" renew --dry-run --non-interactive

certificate_path="/etc/letsencrypt/live/$public_ip/fullchain.pem"
openssl x509 -in "$certificate_path" -noout -ext subjectAltName | \
  grep -F "IP Address:$public_ip" >/dev/null
openssl x509 -in "$certificate_path" -noout -checkend 86400 >/dev/null

tls_tmp="$(mktemp /etc/nginx/.co-story-tls.conf.XXXXXX)"
printf '%s\n' \
  "ssl_certificate /etc/letsencrypt/live/$public_ip/fullchain.pem;" \
  "ssl_certificate_key /etc/letsencrypt/live/$public_ip/privkey.pem;" \
  'ssl_protocols TLSv1.2 TLSv1.3;' \
  'ssl_session_tickets off;' > "$tls_tmp"
chmod 0600 "$tls_tmp"
mv -f "$tls_tmp" /etc/nginx/co-story-tls.conf

runtime_tmp="$(mktemp /etc/co-story/.runtime.env.XXXXXX)"
printf '%s\n' \
  'CO_STORY_ENV=production' \
  'CO_STORY_COOKIE_SECURE=true' \
  "CO_STORY_ALLOWED_HOSTS=$public_ip" \
  "CO_STORY_ALLOWED_ORIGINS=https://$public_ip" \
  'CO_STORY_AWS_REGION=ap-northeast-1' \
  'CO_STORY_BEDROCK_MODEL_ID=amazon.nova-lite-v1:0' \
  "CO_STORY_BEDROCK_GUARDRAIL_ID=$guardrail_id" \
  'CO_STORY_BEDROCK_GUARDRAIL_VERSION=1' \
  'CO_STORY_BEDROCK_MAX_TOKENS=800' > "$runtime_tmp"
chown root:co-story "$runtime_tmp"
chmod 0640 "$runtime_tmp"
mv -f "$runtime_tmp" /etc/co-story/runtime.env

render_nginx_config "$active_release/ops/nginx/co-story-public.conf" \
  /etc/nginx/co-story-public.conf
/usr/sbin/nginx -t -c /etc/nginx/co-story-public.conf
systemctl restart co-story.service
systemctl restart co-story-nginx-public.service
systemctl enable --now co-story-certbot-renew.timer
wait_for_readiness "https://$public_ip/api/v1/ready" "$public_ip" "$public_ip:443:127.0.0.1"

success=1
printf '%s\n' 'public HTTPS enabled'
