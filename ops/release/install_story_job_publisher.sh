#!/bin/bash
set -euo pipefail

stop() {
  printf 'publisher_service=stopped:%s\n' "${1:?reason required}"
  exit 2
}

test_root="${CO_STORY_TEST_ROOT:-}"
case "$test_root" in
  '' | /*) ;;
  *) stop invalid_test_root ;;
esac

host_path() {
  printf '%s%s\n' "$test_root" "${1:?host path required}"
}

[ "$(id -u)" -eq 0 ] || stop must_run_as_root

unit_source="${1:?publisher unit source required}"
action="${2:?action required}"
[ "$action" = install ] || stop invalid_action
[ -f "$unit_source" ] || stop invalid_unit_source
[ ! -L "$unit_source" ] || stop invalid_unit_source
[ "$(stat -c '%U:%G:%a' "$unit_source")" = root:root:400 ] \
  || stop invalid_unit_metadata

service_name=co-story-publisher.service
installed_unit="$(host_path /etc/systemd/system/co-story-publisher.service)"

if systemctl is-active "$service_name" >/dev/null 2>&1; then
  stop service_must_be_inactive
fi

if [ -e "$installed_unit" ] || [ -L "$installed_unit" ]; then
  stop existing_unit_requires_separate_update
fi

install -o root -g root -m 0444 "$unit_source" "$installed_unit"
if ! systemctl daemon-reload; then
  rm -f "$installed_unit"
  systemctl daemon-reload || true
  stop daemon_reload_failed
fi

enablement_state="$(systemctl is-enabled "$service_name" 2>/dev/null || true)"
case "$enablement_state" in
  disabled|static) ;;
  *)
    rm -f "$installed_unit"
    systemctl daemon-reload || true
    stop unexpected_enabled_service
    ;;
esac
if systemctl is-active "$service_name" >/dev/null 2>&1; then
  rm -f "$installed_unit"
  systemctl daemon-reload || true
  stop unexpected_active_service
fi

printf 'publisher_service=installed:disabled\n'
