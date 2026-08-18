#!/usr/bin/env bash
set -euo pipefail

wait_for_readiness() {
  readiness_url="${1:?readiness URL required}"
  readiness_attempts=30
  readiness_attempt=1
  while [ "$readiness_attempt" -le "$readiness_attempts" ]; do
    if curl --fail --silent --max-time 2 --header 'Host: localhost' \
      "$readiness_url" >/dev/null; then
      return 0
    fi
    if [ "$readiness_attempt" -lt "$readiness_attempts" ]; then
      sleep 1
    fi
    readiness_attempt=$((readiness_attempt + 1))
  done
  printf '%s\n' 'staging readiness check failed' >&2
  return 1
}

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'public HTTPS rollback must run as root' >&2
  exit 2
fi

public_ip="${1:?public IPv4 required}"
if ! python3.13 -c \
  'import ipaddress,sys; address=ipaddress.ip_address(sys.argv[1]); raise SystemExit(0 if address.version == 4 and address.is_global else 1)' \
  "$public_ip"; then
  printf '%s\n' 'invalid public IPv4' >&2
  exit 2
fi
state_dir=/var/lib/co-story/public-https
certbot() {
  /opt/co-story/certbot/bin/certbot "$@"
}
test -x /opt/co-story/certbot/bin/certbot
test -f "$state_dir/runtime.env.before-public"

systemctl disable --now co-story-certbot-renew.timer
systemctl disable --now co-story-nginx-public.service
install -m 0640 -o root -g co-story "$state_dir/runtime.env.before-public" \
  /etc/co-story/runtime.env
grep -Fx 'CO_STORY_ENV=staging' /etc/co-story/runtime.env >/dev/null
grep -Fx 'CO_STORY_COOKIE_SECURE=false' /etc/co-story/runtime.env >/dev/null
systemctl restart co-story.service
systemctl enable --now co-story-nginx-staging.service
wait_for_readiness http://127.0.0.1:8080/api/v1/ready

certbot delete --non-interactive --cert-name "$public_ip"
rm -f /etc/nginx/co-story-tls.conf
printf '%s\n' 'public HTTPS disabled; internal staging verified'
