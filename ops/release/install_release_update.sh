#!/usr/bin/env bash
set -euo pipefail

wait_for_readiness() {
  readiness_url="${1:?readiness URL required}"
  readiness_host="${2:?readiness host required}"
  readiness_attempts=30
  readiness_attempt=1
  while [ "$readiness_attempt" -le "$readiness_attempts" ]; do
    if curl --fail --silent --max-time 2 --header "Host: $readiness_host" \
      "$readiness_url" >/dev/null; then
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
  printf '%s\n' 'release update installer must run as root' >&2
  exit 2
fi

# The release is executed by the unprivileged co-story service account. Do not
# inherit a caller's restrictive umask when creating its virtual environment.
umask 0022

release_id="${1:?release id required}"
case "$release_id" in
  *[!A-Za-z0-9._-]* | '')
    printf '%s\n' 'invalid release id' >&2
    exit 2
    ;;
esac

artifact_root="$(pwd)"
archive="$artifact_root/co-story.tar.gz"
checksum_file="$artifact_root/co-story.tar.gz.sha256"
test -f "$archive"
test -f "$checksum_file"
sha256sum -c "$checksum_file"

database_environment=/etc/co-story/database.env
test -s "$database_environment"
if [ "$(stat -c '%U:%G:%a' "$database_environment")" != 'root:co-story:640' ]; then
  printf '%s\n' 'protected database environment has unexpected ownership or mode' >&2
  exit 2
fi

runtime_environment=/etc/co-story/runtime.env
edge_mode=''
health_host=''
if systemctl is-active --quiet co-story-nginx-public.service; then
  edge_mode=public
  test -s "$runtime_environment"
  if [ "$(stat -c '%U:%G:%a' "$runtime_environment")" != 'root:co-story:640' ]; then
    printf '%s\n' 'protected runtime environment has unexpected ownership or mode' >&2
    exit 2
  fi
  allowed_hosts="$(sed -n 's/^CO_STORY_ALLOWED_HOSTS=//p' "$runtime_environment")"
  health_host="${allowed_hosts%%,*}"
  case "$health_host" in
    *[!A-Za-z0-9.-]* | '')
      printf '%s\n' 'runtime environment has invalid allowed host' >&2
      exit 2
      ;;
  esac
elif systemctl is-active --quiet co-story-nginx-staging.service; then
  edge_mode=staging
  health_host=localhost
else
  printf '%s\n' 'no active co-story edge service found' >&2
  exit 2
fi

root=/opt/co-story
releases="$root/releases"
resolved_releases="$(realpath -e "$releases")"
previous_target="$(readlink -f "$root/current" 2>/dev/null || true)"
case "$previous_target" in
  "$resolved_releases"/*)
    test -d "$previous_target"
    ;;
  *)
    printf '%s\n' 'existing active release is invalid' >&2
    exit 2
    ;;
esac

release_dir="$releases/$release_id"
if [ -e "$release_dir" ]; then
  printf '%s\n' 'release directory already exists' >&2
  exit 2
fi

stage="$(mktemp -d "$root/.stage.$release_id.XXXXXX")"
success=0
cleanup() {
  rm -rf "$stage"
  if [ "$success" -eq 0 ]; then
    active_target="$(readlink -f "$root/current" 2>/dev/null || true)"
    if [ "$active_target" != "$release_dir" ]; then
      rm -rf "$release_dir"
    fi
  fi
}
trap cleanup EXIT

restore_previous_release() {
  restore_link="$root/.current.restore.$release_id"
  rm -f "$restore_link"
  ln -s "$previous_target" "$restore_link"
  mv -Tf "$restore_link" "$root/current"
  systemctl restart co-story.service || true
  if [ "$edge_mode" = public ]; then
    systemctl restart co-story-nginx-public.service || true
  else
    systemctl restart co-story-nginx-staging.service || true
  fi
}

verify_active_edge() {
  if [ "$edge_mode" = public ]; then
    systemctl restart co-story-nginx-public.service
    wait_for_readiness "https://$health_host/api/v1/ready" "$health_host"
  else
    systemctl restart co-story-nginx-staging.service
    wait_for_readiness http://127.0.0.1:8080/api/v1/ready localhost
  fi
}

tar -xzf "$archive" -C "$stage"
test -d "$stage/co-story/backend"
mv "$stage/co-story" "$release_dir"

python3.13 -m venv "$release_dir/.venv"
"$release_dir/.venv/bin/python" -m pip install --no-deps \
  --requirement "$release_dir/backend/requirements-prod.txt"

install -m 0644 "$release_dir/ops/systemd/co-story.service" \
  /etc/systemd/system/co-story.service
install -m 0644 "$release_dir/ops/systemd/co-story-candidate@.service" \
  /etc/systemd/system/co-story-candidate@.service
install -m 0644 "$release_dir/ops/systemd/co-story-migrate@.service" \
  /etc/systemd/system/co-story-migrate@.service
install -m 0644 "$release_dir/ops/systemd/co-story-nginx-staging.service" \
  /etc/systemd/system/co-story-nginx-staging.service
install -m 0644 "$release_dir/ops/systemd/co-story-nginx-public.service" \
  /etc/systemd/system/co-story-nginx-public.service
install -m 0644 "$release_dir/ops/nginx/co-story-staging.conf" \
  /etc/nginx/co-story-staging.conf
systemctl daemon-reload

"$release_dir/ops/release/activate.sh" "$release_id" "$health_host"
if ! verify_active_edge; then
  restore_previous_release
  printf '%s\n' "release update failed $edge_mode edge verification; previous release restored" >&2
  exit 1
fi

success=1
printf '%s\n' "release update installed; $edge_mode edge verified"
