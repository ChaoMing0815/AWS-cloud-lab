#!/usr/bin/env bash
set -euo pipefail

ROOT=/opt/co-story
RELEASES="$ROOT/releases"
release_id="${1:?release id required}"

case "$release_id" in
  *[!A-Za-z0-9._-]* | '')
    printf '%s\n' 'invalid release id' >&2
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
previous_target="$(readlink -f "$ROOT/current")"
candidate_active=0

cleanup_candidate() {
  if [ "$candidate_active" -eq 1 ]; then
    systemctl stop "$candidate_unit" || true
  fi
}
trap cleanup_candidate EXIT

systemctl start "co-story-migrate@$release_id.service"
candidate_unit="co-story-candidate@$release_id.service"
systemctl start "$candidate_unit"
candidate_active=1
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8001/api/v1/ready >/dev/null
cleanup_candidate
candidate_active=0

stage_link="$ROOT/.current.$release_id"
rm -f "$stage_link"
ln -s "$resolved_release" "$stage_link"
previous_link="$ROOT/.current.previous.$release_id"
rm -f "$previous_link"
ln -s "$previous_target" "$previous_link"
mv -Tf "$previous_link" "$ROOT/current.previous"
mv -Tf "$stage_link" "$ROOT/current"

if ! systemctl restart co-story.service; then
  restore_link="$ROOT/.current.restore.$release_id"
  rm -f "$restore_link"
  ln -s "$previous_target" "$restore_link"
  mv -Tf "$restore_link" "$ROOT/current"
  systemctl restart co-story.service || true
  exit 1
fi

if ! curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/api/v1/ready >/dev/null; then
  restore_link="$ROOT/.current.restore.$release_id"
  rm -f "$restore_link"
  ln -s "$previous_target" "$restore_link"
  mv -Tf "$restore_link" "$ROOT/current"
  systemctl restart co-story.service || true
  exit 1
fi
