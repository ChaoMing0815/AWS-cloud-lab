#!/usr/bin/env bash
set -euo pipefail

output_path="${1:-/var/log/co-story/system.jsonl}"
systemctl_bin="${2:-/usr/bin/systemctl}"

if [ -L "$output_path" ]; then
  printf '%s\n' 'system health log target must not be a symlink' >&2
  exit 2
fi

normalize_state() {
  case "$1" in
    active | inactive | failed | activating | deactivating)
      printf '%s' "$1"
      ;;
    *)
      printf '%s' 'unknown'
      ;;
  esac
}

service_state() {
  raw_state="$($systemctl_bin is-active "$1" 2>/dev/null || true)"
  normalize_state "$raw_state"
}

application="$(service_state co-story.service)"
cloudwatch_agent="$(service_state amazon-cloudwatch-agent.service)"
public_edge="$(service_state co-story-nginx-public.service)"
if [ "$public_edge" != 'active' ]; then
  staging_edge="$(service_state co-story-nginx-staging.service)"
  if [ "$staging_edge" = 'active' ]; then
    public_edge='active'
  fi
fi

umask 0027
mkdir -p "$(dirname "$output_path")"
/usr/bin/python3 - "$output_path" "$application" "$cloudwatch_agent" "$public_edge" <<'PY'
import json
import os
import sys

path, application, cloudwatch_agent, public_edge = sys.argv[1:]
flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
if hasattr(os, "O_NOFOLLOW"):
    flags |= os.O_NOFOLLOW
descriptor = os.open(path, flags, 0o640)
try:
    payload = {
        "event_type": "system_health",
        "application": application,
        "cloudwatch_agent": cloudwatch_agent,
        "public_edge": public_edge,
    }
    os.write(
        descriptor,
        (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"),
    )
finally:
    os.close(descriptor)
PY
chmod 0640 "$output_path"
if [ "$output_path" = '/var/log/co-story/system.jsonl' ]; then
  chown root:co-story "$output_path"
fi
