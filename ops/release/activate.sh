#!/usr/bin/env bash
set -euo pipefail

wait_for_readiness() {
  readiness_url="${1:?readiness URL required}"
  readiness_host="${2:?readiness host required}"
  readiness_attempts=30
  readiness_attempt=1
  while [ "$readiness_attempt" -le "$readiness_attempts" ]; do
    if curl --fail --silent --max-time 2 \
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

ROOT=/opt/co-story
RELEASES="$ROOT/releases"
release_id="${1:?release id required}"
health_host="${2:-localhost}"

case "$release_id" in
  *[!A-Za-z0-9._-]* | '')
    printf '%s\n' 'invalid release id' >&2
    exit 2
    ;;
esac
case "$health_host" in
  *[!A-Za-z0-9.-]* | '')
    printf '%s\n' 'invalid health host' >&2
    exit 2
    ;;
esac

release_dir="$RELEASES/$release_id"
resolved_release="$(realpath -e "$release_dir")"
resolved_releases="$(realpath -e "$RELEASES")"
case "$resolved_release" in
  "$resolved_releases"/*) ;;
  *)
    printf '%s\n' 'release must be inside releases directory' >&2
    exit 2
    ;;
esac

test -x "$resolved_release/.venv/bin/python"
test -x "$resolved_release/.venv/bin/uvicorn"
previous_target=""
had_previous=0
if [ -L "$ROOT/current" ]; then
  previous_candidate="$(readlink -f "$ROOT/current" 2>/dev/null || true)"
  case "$previous_candidate" in
    "$resolved_releases"/*)
      if [ -d "$previous_candidate" ]; then
        previous_target="$previous_candidate"
        had_previous=1
      fi
      ;;
  esac
fi
candidate_active=0

cleanup_candidate() {
  if [ "$candidate_active" -eq 1 ]; then
    systemctl stop "$candidate_unit" || true
  fi
}
trap cleanup_candidate EXIT

restore_previous() {
  if [ "$had_previous" -eq 1 ]; then
    restore_link="$ROOT/.current.restore.$release_id"
    rm -f "$restore_link"
    ln -s "$previous_target" "$restore_link"
    mv -Tf "$restore_link" "$ROOT/current"
    systemctl restart co-story.service || true
  else
    # remove unverified first deployment instead of leaving it active
    rm -f "$ROOT/current"
    systemctl stop co-story.service || true
  fi
}

systemctl start "co-story-migrate@$release_id.service"
candidate_unit="co-story-candidate@$release_id.service"
systemctl start "$candidate_unit"
candidate_active=1
wait_for_readiness http://127.0.0.1:8001/api/v1/ready "$health_host"
cleanup_candidate
candidate_active=0

stage_link="$ROOT/.current.$release_id"
rm -f "$stage_link"
ln -s "$resolved_release" "$stage_link"
if [ "$had_previous" -eq 1 ]; then
  previous_link="$ROOT/.current.previous.$release_id"
  rm -f "$previous_link"
  ln -s "$previous_target" "$previous_link"
  mv -Tf "$previous_link" "$ROOT/current.previous"
fi
mv -Tf "$stage_link" "$ROOT/current"

if ! systemctl restart co-story.service; then
  restore_previous
  exit 1
fi

if ! wait_for_readiness http://127.0.0.1:8000/api/v1/ready "$health_host"; then
  restore_previous
  exit 1
fi
