#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'container release must run as root' >&2
  exit 2
fi

repository_uri="${1:?repository URI required}"
image_digest="${2:?image digest required}"
previous_image_digest="${3:?previous image digest required}"
health_host="${4:?health host required}"

case "$repository_uri" in
  '' | *[!A-Za-z0-9./_-]* | *..*)
    printf '%s\n' 'invalid repository URI' >&2
    exit 2
    ;;
esac
if [[ ! "$image_digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  printf '%s\n' 'invalid image digest' >&2
  exit 2
fi
if [[ ! "$previous_image_digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  printf '%s\n' 'invalid previous image digest' >&2
  exit 2
fi
if [ "$image_digest" = "$previous_image_digest" ]; then
  printf '%s\n' 'target and previous image digests must differ' >&2
  exit 2
fi
case "$health_host" in
  *[!A-Za-z0-9.-]* | '')
    printf '%s\n' 'invalid health host' >&2
    exit 2
    ;;
esac

readonly target_image="$repository_uri@$image_digest"
readonly previous_image="$repository_uri@$previous_image_digest"
readonly registry="${repository_uri%%/*}"
readonly release_env=/etc/co-story/container-release.env
readonly runtime_env=/etc/co-story/runtime.env
readonly database_env=/etc/co-story/database.env
readonly log_dir=/var/log/co-story
readonly script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly container_unit="$script_root/ops/systemd/co-story-container.service"

test -s "$runtime_env"
test -s "$database_env"
test -f "$container_unit"
install -d -m 0750 -o co-story -g co-story "$log_dir"

wait_for_health() {
  port="${1:?port required}"
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if curl --fail --silent --show-error --max-time 3 \
      --header "Host: $health_host" "http://127.0.0.1:$port/api/v1/live" >/dev/null \
      && curl --fail --silent --show-error --max-time 3 \
        --header "Host: $health_host" "http://127.0.0.1:$port/api/v1/ready" >/dev/null; then
      return 0
    fi
    if [ "$attempt" -lt 30 ]; then
      sleep 1
    fi
    attempt=$((attempt + 1))
  done
  printf 'container_health=failed port=%s\n' "$port" >&2
  return 1
}

write_release_env() {
  image_ref="${1:?image reference required}"
  temporary="$(mktemp /etc/co-story/.container-release.XXXXXX)"
  printf 'CO_STORY_CONTAINER_IMAGE=%s\n' "$image_ref" >"$temporary"
  chown root:root "$temporary"
  chmod 0600 "$temporary"
  mv -f "$temporary" "$release_env"
}

restore_previous() {
  docker rm -f co-story-candidate >/dev/null 2>&1 || true
  write_release_env "$previous_image"
  systemctl restart co-story.service || true
  wait_for_health 8000 || true
}

aws ecr get-login-password --region ap-northeast-1 \
  | docker login --username AWS --password-stdin "$registry" >/dev/null
docker pull "$previous_image"
docker pull "$target_image"

if [ ! -s "$release_env" ]; then
  install -m 0644 "$container_unit" /etc/systemd/system/co-story.service
  write_release_env "$previous_image"
  systemctl daemon-reload
  systemctl restart co-story.service
  wait_for_health 8000
else
  expected="CO_STORY_CONTAINER_IMAGE=$previous_image"
  if [ "$(cat "$release_env")" != "$expected" ]; then
    printf '%s\n' 'previous image does not match active release' >&2
    exit 2
  fi
fi

docker run --rm --network host --read-only --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env-file "$runtime_env" --env-file "$database_env" \
  --mount "type=bind,src=$log_dir,dst=/var/log/co-story" \
  --user 10001:10001 --entrypoint python "$target_image" -m app.commands.migrate

docker rm -f co-story-candidate >/dev/null 2>&1 || true
docker run --detach --name co-story-candidate --network host --read-only \
  --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m --env-file "$runtime_env" \
  --env-file "$database_env" \
  --env CO_STORY_APPLICATION_LOG_PATH=/var/log/co-story/candidate.jsonl \
  --mount "type=bind,src=$log_dir,dst=/var/log/co-story" --user 10001:10001 \
  "$target_image" uvicorn app.main:create_app --factory --host 127.0.0.1 \
  --port 8001 --workers 1 >/dev/null
if ! wait_for_health 8001; then
  docker rm -f co-story-candidate >/dev/null 2>&1 || true
  exit 1
fi
docker rm -f co-story-candidate >/dev/null

write_release_env "$target_image"
if ! systemctl restart co-story.service; then
  restore_previous
  exit 1
fi
if ! wait_for_health 8000; then
  restore_previous
  exit 1
fi

printf 'container_release=verified image_digest=%s previous_image_digest=%s\n' \
  "$image_digest" "$previous_image_digest"
