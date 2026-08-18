#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'certificate renewal must run as root' >&2
  exit 2
fi

certbot() {
  /opt/co-story/certbot/bin/certbot "$@"
}
test -x /opt/co-story/certbot/bin/certbot

certbot renew --quiet
/usr/sbin/nginx -t -c /etc/nginx/co-story-public.conf
systemctl reload co-story-nginx-public.service
