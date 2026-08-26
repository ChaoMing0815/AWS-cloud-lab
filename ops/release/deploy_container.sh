#!/usr/bin/env bash
set -euo pipefail

readonly expected_legacy_release=tier1-20260825-4a51e0e
readonly test_root="${CO_STORY_TEST_ROOT:-}"

fail() {
  printf 'container_release=stopped reason=%s\n' "${1:?reason required}" >&2
  return 2
}

host_path() {
  absolute="${1:?absolute path required}"
  case "$absolute" in
    /*) printf '%s%s\n' "$test_root" "$absolute" ;;
    *) fail invalid_host_path ;;
  esac
}

record_event() {
  if [ -n "${CO_STORY_TEST_EVENT_LOG:-}" ]; then
    printf '%s\n' "${1:?event required}" >>"$CO_STORY_TEST_EVENT_LOG"
  fi
}

failure_enabled() {
  wanted="${1:?failure label required}"
  failures=",${CO_STORY_TEST_FAIL:-},"
  case "$failures" in *",$wanted,"*) return 0 ;; *) return 1 ;; esac
}

mutation_guard() {
  label="${1:?mutation label required}"
  record_event "mutation-attempt:$label"
  ! failure_enabled "$label"
}

file_metadata() {
  kind="${1:?metadata kind required}"
  path="${2:?metadata path required}"
  if [ -n "$test_root" ]; then
    case "$kind" in
      runtime) printf '%s\n' "${CO_STORY_TEST_RUNTIME_METADATA:-root:co-story:640}" ;;
      database) printf '%s\n' "${CO_STORY_TEST_DATABASE_METADATA:-root:co-story:640}" ;;
      state) printf '%s\n' 'root:root:600' ;;
      *) printf '%s\n' 'root:root:600' ;;
    esac
  else
    stat -c '%U:%G:%a' "$path"
  fi
}

file_sha256() {
  path="${1:?file required}"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
  else
    shasum -a 256 "$path" | awk '{print $1}'
  fi
}

atomic_install() {
  source="${1:?source required}"
  destination="${2:?destination required}"
  mode="${3:?mode required}"
  directory="$(dirname "$destination")"
  if [ ! -d "$directory" ]; then install -d -m 0755 "$directory"; fi
  temporary="$(mktemp "$directory/.co-story-install.XXXXXX")"
  if ! install -m "$mode" "$source" "$temporary"; then
    rm -f "$temporary"
    return 1
  fi
  if [ -z "$test_root" ]; then
    if ! chown root:root "$temporary"; then rm -f "$temporary"; return 1; fi
  fi
  if ! mv -f "$temporary" "$destination"; then rm -f "$temporary"; return 1; fi
}

atomic_write() {
  destination="${1:?destination required}"
  mode="${2:?mode required}"
  content="${3-}"
  directory="$(dirname "$destination")"
  if [ ! -d "$directory" ]; then install -d -m 0755 "$directory"; fi
  temporary="$(mktemp "$directory/.co-story-state.XXXXXX")"
  if ! printf '%s' "$content" >"$temporary"; then rm -f "$temporary"; return 1; fi
  if ! chmod "$mode" "$temporary"; then rm -f "$temporary"; return 1; fi
  if [ -z "$test_root" ]; then
    if ! chown root:root "$temporary"; then rm -f "$temporary"; return 1; fi
  fi
  if ! mv -f "$temporary" "$destination"; then rm -f "$temporary"; return 1; fi
}

wait_for_health() {
  label="${1:?health label required}"
  port="${2:?port required}"
  record_event "health:$label:$port"
  if failure_enabled "$label"; then return 1; fi
  if failure_enabled target-and-legacy-restore; then
    if [ "$label" = target-active ] || [ "$label" = legacy-restore ]; then return 1; fi
  fi
  if [ -n "$test_root" ]; then
    return 0
  fi
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if curl --fail --silent --show-error --max-time 3 \
      --header "Host: $health_host" "http://127.0.0.1:$port/api/v1/live" >/dev/null \
      && curl --fail --silent --show-error --max-time 3 \
        --header "Host: $health_host" "http://127.0.0.1:$port/api/v1/ready" >/dev/null; then
      return 0
    fi
    if [ "$attempt" -lt 30 ]; then sleep 1; fi
    attempt=$((attempt + 1))
  done
  return 1
}

restart_service() {
  label="${1:?restart label required}"
  if failure_enabled "$label"; then
    return 1
  fi
  systemctl restart co-story.service
}

write_release_env() {
  image="${1:?image required}"
  atomic_write "$release_env" 0600 "CO_STORY_CONTAINER_IMAGE=$image
"
}

write_transition_state() {
  status="${1:?state required}"
  image="${2:?container image required}"
  atomic_write "$transition_state" 0600 "STATE=$status
LEGACY_RELEASE_ID=$expected_legacy_release
LEGACY_RELEASE_TARGET=$legacy_release
LEGACY_UNIT_SHA256=$legacy_unit_sha
DRIVER_SHA256=$driver_sha
CONTAINER_UNIT_SHA256=$container_unit_sha
CONTAINER_IMAGE=$image
"
}

state_value() {
  key="${1:?state key required}"
  value="$(awk -F= -v key="$key" '$1 == key {print substr($0, length(key) + 2)}' "$transition_state")"
  lines="$(awk -F= -v key="$key" '$1 == key {count++} END {print count + 0}' "$transition_state")"
  [ "$lines" -eq 1 ] || fail duplicate_or_missing_state_key
  printf '%s\n' "$value"
}

load_container_state() {
  [ -s "$transition_state" ] || fail missing_transition_state
  [ "$(file_metadata state "$transition_state")" = root:root:600 ] || fail invalid_transition_state_metadata
  [ "$(wc -l <"$transition_state" | tr -d ' ')" -eq 7 ] || fail invalid_transition_state_shape
  state_status="$(state_value STATE)"
  state_legacy_id="$(state_value LEGACY_RELEASE_ID)"
  state_legacy_release="$(state_value LEGACY_RELEASE_TARGET)"
  state_legacy_unit_sha="$(state_value LEGACY_UNIT_SHA256)"
  state_driver_sha="$(state_value DRIVER_SHA256)"
  state_container_unit_sha="$(state_value CONTAINER_UNIT_SHA256)"
  state_container_image="$(state_value CONTAINER_IMAGE)"
  [ "$state_legacy_id" = "$expected_legacy_release" ] || fail legacy_state_mismatch
  [ "$state_legacy_release" = "$legacy_release" ] || fail legacy_release_state_mismatch
  [[ "$state_legacy_unit_sha" =~ ^[a-f0-9]{64}$ ]] || fail invalid_legacy_unit_checksum
  [[ "$state_driver_sha" =~ ^[a-f0-9]{64}$ ]] || fail invalid_driver_checksum
  [[ "$state_container_unit_sha" =~ ^[a-f0-9]{64}$ ]] || fail invalid_container_unit_checksum
  [[ "$state_container_image" =~ ^${repository_uri}@sha256:[a-f0-9]{64}$ ]] || fail invalid_state_image
}

validate_common_host() {
  [ -s "$runtime_env" ] || fail missing_runtime_env
  [ -s "$database_env" ] || fail missing_database_env
  [ "$(file_metadata runtime "$runtime_env")" = root:co-story:640 ] || fail invalid_runtime_env_metadata
  [ "$(file_metadata database "$database_env")" = root:co-story:640 ] || fail invalid_database_env_metadata
  [ "$(readlink -f "$current_link" 2>/dev/null || true)" = "$legacy_release" ] || fail active_legacy_symlink_mismatch
  [ -f "$legacy_release/ops/systemd/co-story.service" ] || fail missing_legacy_unit
  [ -d "$log_dir" ] || fail missing_log_directory
  command -v docker >/dev/null 2>&1 || fail docker_not_installed
  systemctl is-active --quiet docker.service || fail docker_not_active
}

start_legacy_candidate() {
  if systemctl is-active --quiet co-story-legacy-candidate.service; then
    fail existing_legacy_candidate
  fi
  systemd-run --unit=co-story-legacy-candidate --collect \
    --property=Type=exec --property=User=co-story --property=Group=co-story \
    --property="WorkingDirectory=$legacy_release/backend" \
    --property="EnvironmentFile=$runtime_env" \
    --property="EnvironmentFile=$database_env" \
    --property=NoNewPrivileges=yes --property=PrivateTmp=yes \
    --property=ProtectSystem=strict --property=ProtectHome=yes \
    --property="ReadWritePaths=$log_dir" --property=Restart=no \
    "$legacy_release/.venv/bin/uvicorn" app.main:create_app --factory \
    --host 127.0.0.1 --port 8001 --workers 1 >/dev/null
}

login_registry() {
  aws ecr get-login-password --region ap-northeast-1 \
    | docker login --username AWS --password-stdin "$registry" >/dev/null
}

run_migration() {
  record_event migration
  docker run --rm --network host --read-only --cap-drop ALL \
    --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --env-file "$runtime_env" --env-file "$database_env" \
    --mount "type=bind,src=$log_dir,dst=/var/log/co-story" \
    --user 10001:10001 --entrypoint python "$target_image" -m app.commands.migrate
}

check_target_candidate() {
  docker rm -f co-story-candidate >/dev/null 2>&1 || true
  docker run --detach --name co-story-candidate --network host --read-only \
    --cap-drop ALL --security-opt no-new-privileges \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m --env-file "$runtime_env" \
    --env-file "$database_env" \
    --env CO_STORY_APPLICATION_LOG_PATH=/var/log/co-story/candidate.jsonl \
    --mount "type=bind,src=$log_dir,dst=/var/log/co-story" --user 10001:10001 \
    "$target_image" uvicorn app.main:create_app --factory --host 127.0.0.1 \
    --port 8001 --workers 1 >/dev/null
  if ! wait_for_health target-candidate 8001; then
    docker rm -f co-story-candidate >/dev/null 2>&1 || true
    return 1
  fi
  docker rm -f co-story-candidate >/dev/null
}

mark_legacy_mutation_restore_failed() {
  rm -f "$release_env"
  write_transition_state legacy-mutation-restore-failed "$target_image" || true
}

cleanup_bootstrap_transaction() {
  cleanup_failed=0
  for exact_path in \
    "$release_env" "$transition_state" "$stable_driver" \
    "$stable_container_unit" "$legacy_unit_backup"; do
    if ! rm -f "$exact_path"; then cleanup_failed=1; fi
  done
  [ "$cleanup_failed" -eq 0 ] || return 1
  for exact_path in \
    "$release_env" "$transition_state" "$stable_driver" \
    "$stable_container_unit" "$legacy_unit_backup"; do
    [ ! -e "$exact_path" ] || return 1
  done
}

rollback_legacy_mutation() {
  record_event mutation:restore-legacy-unit
  restore_source="$legacy_release/ops/systemd/co-story.service"
  if [ -s "$legacy_unit_backup" ]; then restore_source="$legacy_unit_backup"; fi
  if ! atomic_install "$restore_source" "$installed_unit" 0644 \
    || ! systemctl daemon-reload \
    || ! restart_service legacy-restore-restart \
    || ! wait_for_health legacy-restore 8000 \
    || [ "$(file_sha256 "$installed_unit")" != "$legacy_unit_sha" ]; then
    mark_legacy_mutation_restore_failed
    return 1
  fi
  if ! cleanup_bootstrap_transaction; then
    mark_legacy_mutation_restore_failed
    return 1
  fi
}

bootstrap_mutation_failed() {
  reason="${1:?failure reason required}"
  if ! rollback_legacy_mutation; then
    fail legacy_mutation_restore_failed
    return $?
  fi
  fail "bootstrap_mutation_$reason"
}

mark_asset_restore_failed() {
  driver_sha="$previous_driver_sha"
  container_unit_sha="$previous_unit_sha"
  write_transition_state asset-restore-failed "$previous_image" || true
}

cleanup_previous_asset_backups() {
  backup_cleanup_failed=0
  for exact_path in "$previous_driver_backup" "$previous_unit_backup"; do
    if ! rm -f "$exact_path"; then backup_cleanup_failed=1; fi
  done
  [ "$backup_cleanup_failed" -eq 0 ] || return 1
  [ ! -e "$previous_driver_backup" ] && [ ! -e "$previous_unit_backup" ]
}

restore_previous_assets_and_container() {
  record_event mutation:restore-previous-assets
  driver_sha="$previous_driver_sha"
  container_unit_sha="$previous_unit_sha"
  if ! atomic_install "$previous_driver_backup" "$stable_driver" 0755 \
    || ! atomic_install "$previous_unit_backup" "$stable_container_unit" 0644 \
    || ! atomic_install "$previous_unit_backup" "$installed_unit" 0644 \
    || ! systemctl daemon-reload \
    || ! write_release_env "$previous_image" \
    || ! restart_service previous-restore-restart \
    || ! wait_for_health previous-restore 8000 \
    || ! write_transition_state container-active "$previous_image"; then
    mark_asset_restore_failed
    return 1
  fi
  if ! cleanup_previous_asset_backups; then
    mark_asset_restore_failed
    return 1
  fi
}

legacy_bootstrap() {
  [ -z "$previous_image_digest" ] || fail bootstrap_must_not_have_previous_digest
  [ "$legacy_release_id" = "$expected_legacy_release" ] || fail unexpected_legacy_release
  validate_common_host
  [ ! -e "$transition_state" ] || fail existing_transition_state
  [ ! -e "$release_env" ] || fail existing_container_release_env
  [ ! -e "$legacy_unit_backup" ] || fail existing_legacy_unit_backup
  [ ! -e "$stable_driver" ] || fail existing_stable_driver
  [ ! -e "$stable_container_unit" ] || fail existing_stable_container_unit
  [ -f "$container_unit_source" ] || fail missing_container_unit_asset
  [ -f "$driver_asset_source" ] || fail missing_driver_asset
  cmp -s "$installed_unit" "$legacy_release/ops/systemd/co-story.service" || fail installed_legacy_unit_mismatch
  legacy_unit_sha="$(file_sha256 "$installed_unit")"
  driver_sha="$(file_sha256 "$driver_asset_source")"
  container_unit_sha="$(file_sha256 "$container_unit_source")"
  wait_for_health legacy-preflight 8000 || fail legacy_preflight_unhealthy

  login_registry
  docker pull "$target_image" >/dev/null
  run_migration || fail migration_failed
  wait_for_health legacy-post-migration 8000 || fail legacy_not_backward_compatible
  check_target_candidate || fail target_candidate_unhealthy

  if [ "${CO_STORY_TEST_STALE_FENCE:-}" = unit ]; then printf '# stale\n' >>"$installed_unit"; fi
  [ "$(readlink -f "$current_link" 2>/dev/null || true)" = "$legacy_release" ] || fail stale_legacy_symlink
  [ "$(file_sha256 "$installed_unit")" = "$legacy_unit_sha" ] || fail stale_legacy_unit

  if ! atomic_install "$installed_unit" "$legacy_unit_backup" 0600; then
    bootstrap_mutation_failed legacy-backup-install
    return $?
  fi
  if ! mutation_guard stable-driver-install \
    || ! atomic_install "$driver_asset_source" "$stable_driver" 0755; then
    bootstrap_mutation_failed stable-driver-install
    return $?
  fi
  if ! atomic_install "$container_unit_source" "$stable_container_unit" 0644; then
    bootstrap_mutation_failed stable-unit-install
    return $?
  fi
  if ! mutation_guard state-write \
    || ! write_transition_state legacy-switch-pending "$target_image"; then
    bootstrap_mutation_failed state-write
    return $?
  fi
  if ! mutation_guard release-env-write || ! write_release_env "$target_image"; then
    bootstrap_mutation_failed release-env-write
    return $?
  fi
  record_event mutation:install-container-unit
  if ! mutation_guard container-unit-install \
    || ! atomic_install "$container_unit_source" "$installed_unit" 0644; then
    bootstrap_mutation_failed container-unit-install
    return $?
  fi
  if ! mutation_guard daemon-reload || ! systemctl daemon-reload; then
    bootstrap_mutation_failed daemon-reload
    return $?
  fi
  if ! restart_service target-restart || ! wait_for_health target-active 8000; then
    if ! rollback_legacy_mutation; then fail legacy_restore_failed; fi
    fail target_activation_failed
  fi
  if ! write_transition_state container-active "$target_image"; then
    bootstrap_mutation_failed final-state-write
    return $?
  fi
  printf 'container_release=verified mode=legacy-bootstrap image_digest=%s\n' "$image_digest"
}

digest_release() {
  [ -z "$legacy_release_id" ] || fail digest_release_must_not_set_legacy_release
  [[ "$previous_image_digest" =~ ^sha256:[a-f0-9]{64}$ ]] || fail digest_release_requires_previous_digest
  if [ "$image_digest" = "$previous_image_digest" ]; then
    fail target_and_previous_must_differ
  fi
  validate_common_host
  load_container_state
  [ "$state_status" = container-active ] || fail container_state_not_active
  previous_image="$repository_uri@$previous_image_digest"
  [ "$state_container_image" = "$previous_image" ] || fail previous_digest_state_mismatch
  [ "$(cat "$release_env" 2>/dev/null || true)" = "CO_STORY_CONTAINER_IMAGE=$previous_image" ] || fail active_release_env_mismatch
  [ "$(file_sha256 "$installed_unit")" = "$state_container_unit_sha" ] || fail active_container_unit_mismatch
  [ "$(file_sha256 "$stable_driver")" = "$state_driver_sha" ] || fail active_driver_asset_mismatch
  [ "$(file_sha256 "$stable_container_unit")" = "$state_container_unit_sha" ] || fail active_unit_asset_mismatch
  [ -f "$container_unit_source" ] || fail missing_container_unit_asset
  [ -f "$driver_asset_source" ] || fail missing_driver_asset
  [ ! -e "$previous_driver_backup" ] || fail existing_previous_driver_backup
  [ ! -e "$previous_unit_backup" ] || fail existing_previous_unit_backup
  legacy_unit_sha="$state_legacy_unit_sha"
  previous_driver_sha="$state_driver_sha"
  previous_unit_sha="$state_container_unit_sha"
  driver_sha="$previous_driver_sha"
  container_unit_sha="$previous_unit_sha"
  target_driver_sha="$(file_sha256 "$driver_asset_source")"
  target_unit_sha="$(file_sha256 "$container_unit_source")"
  if [ "$release_action" = preflight-only ]; then
    printf 'container_release=preflight-verified mode=digest-release previous_image_digest=%s\n' "$previous_image_digest"
    return 0
  fi
  [ "$release_action" = release ] || fail invalid_release_action
  state_fence="$(file_sha256 "$transition_state")"
  unit_fence="$(file_sha256 "$installed_unit")"
  driver_fence="$(file_sha256 "$stable_driver")"
  stable_unit_fence="$(file_sha256 "$stable_container_unit")"

  login_registry
  docker pull "$previous_image" >/dev/null
  docker pull "$target_image" >/dev/null
  run_migration || fail migration_failed
  wait_for_health previous-post-migration 8000 || fail previous_not_backward_compatible
  check_target_candidate || fail target_candidate_unhealthy

  if [ "${CO_STORY_TEST_STALE_FENCE:-}" = unit ]; then printf '# stale\n' >>"$installed_unit"; fi
  [ "$(file_sha256 "$transition_state")" = "$state_fence" ] || fail stale_transition_state
  [ "$(file_sha256 "$installed_unit")" = "$unit_fence" ] || fail stale_container_unit
  [ "$(file_sha256 "$stable_driver")" = "$driver_fence" ] || fail stale_driver_asset
  [ "$(file_sha256 "$stable_container_unit")" = "$stable_unit_fence" ] || fail stale_unit_asset
  [ "$(cat "$release_env")" = "CO_STORY_CONTAINER_IMAGE=$previous_image" ] || fail stale_release_env

  if ! atomic_install "$stable_driver" "$previous_driver_backup" 0600 \
    || ! atomic_install "$stable_container_unit" "$previous_unit_backup" 0600; then
    if ! cleanup_previous_asset_backups; then mark_asset_restore_failed; fi
    fail asset_backup_failed
    return $?
  fi
  if ! write_transition_state digest-switch-pending "$target_image" \
    || ! write_release_env "$target_image"; then
    if ! restore_previous_assets_and_container; then fail previous_asset_restore_failed; fi
    fail digest_switch_prepare_failed
  fi
  if ! restart_service target-restart || ! wait_for_health target-active 8000; then
    if ! restore_previous_assets_and_container; then fail previous_container_restore_failed; fi
    fail target_activation_failed
  fi
  record_event mutation:promote-stable-assets
  if ! write_transition_state asset-promotion-pending "$target_image" \
    || ! mutation_guard asset-promotion \
    || ! atomic_install "$driver_asset_source" "$stable_driver" 0755 \
    || ! atomic_install "$container_unit_source" "$stable_container_unit" 0644 \
    || ! atomic_install "$container_unit_source" "$installed_unit" 0644 \
    || ! systemctl daemon-reload \
    || ! restart_service target-promoted-restart \
    || ! wait_for_health target-promoted 8000; then
    if ! restore_previous_assets_and_container; then fail previous_asset_restore_failed; fi
    fail asset_promotion_failed
  fi
  driver_sha="$target_driver_sha"
  container_unit_sha="$target_unit_sha"
  if ! write_transition_state container-active "$target_image"; then
    driver_sha="$previous_driver_sha"
    container_unit_sha="$previous_unit_sha"
    if ! restore_previous_assets_and_container; then fail previous_asset_restore_failed; fi
    fail final_state_write_failed
  fi
  if ! cleanup_previous_asset_backups; then
    write_transition_state asset-backup-cleanup-failed "$target_image" || true
    fail asset_backup_cleanup_failed
  fi
  printf 'container_release=verified mode=digest-release image_digest=%s previous_image_digest=%s\n' \
    "$image_digest" "$previous_image_digest"
}

legacy_rollback() {
  [ -z "$previous_image_digest" ] || fail legacy_rollback_must_not_have_previous
  [ "$legacy_release_id" = "$expected_legacy_release" ] || fail unexpected_legacy_release
  validate_common_host
  load_container_state
  [ "$state_status" = container-active ] || fail container_state_not_active
  [ "$state_container_image" = "$target_image" ] || fail active_digest_state_mismatch
  [ "$(cat "$release_env" 2>/dev/null || true)" = "CO_STORY_CONTAINER_IMAGE=$target_image" ] || fail active_release_env_mismatch
  [ "$(file_sha256 "$stable_driver")" = "$state_driver_sha" ] || fail active_driver_asset_mismatch
  [ "$(file_sha256 "$stable_container_unit")" = "$state_container_unit_sha" ] || fail active_unit_asset_mismatch
  [ "$(file_sha256 "$installed_unit")" = "$state_container_unit_sha" ] || fail active_container_unit_mismatch
  [ "$(file_sha256 "$legacy_unit_backup")" = "$state_legacy_unit_sha" ] || fail legacy_unit_backup_mismatch
  [ "$(file_sha256 "$container_unit_source")" = "$state_container_unit_sha" ] || fail container_unit_asset_mismatch
  legacy_unit_sha="$state_legacy_unit_sha"
  driver_sha="$state_driver_sha"
  container_unit_sha="$state_container_unit_sha"
  state_fence="$(file_sha256 "$transition_state")"
  unit_fence="$(file_sha256 "$installed_unit")"

  start_legacy_candidate
  if ! wait_for_health legacy-candidate 8001; then
    systemctl stop co-story-legacy-candidate.service || true
    fail legacy_candidate_not_schema_compatible
  fi
  systemctl stop co-story-legacy-candidate.service
  [ "$(file_sha256 "$transition_state")" = "$state_fence" ] || fail stale_transition_state
  [ "$(file_sha256 "$installed_unit")" = "$unit_fence" ] || fail stale_container_unit
  [ "$(cat "$release_env")" = "CO_STORY_CONTAINER_IMAGE=$target_image" ] || fail stale_release_env

  record_event mutation:install-legacy-unit
  atomic_install "$legacy_unit_backup" "$installed_unit" 0644
  systemctl daemon-reload
  if ! restart_service legacy-target-restart || ! wait_for_health legacy-target 8000; then
    atomic_install "$container_unit_source" "$installed_unit" 0644
    systemctl daemon-reload
    if ! restart_service container-restore-restart || ! wait_for_health container-restore 8000; then
      write_transition_state container-restore-failed "$target_image"
      fail container_restore_after_legacy_failure_failed
    fi
    fail legacy_activation_failed
  fi
  write_transition_state legacy-active "$target_image"
  printf 'container_release=verified mode=legacy-rollback legacy_release=%s\n' "$expected_legacy_release"
}

if [ "$(id -u)" -ne 0 ]; then fail must_run_as_root; exit $?; fi

mode="${1:?release mode required}"
repository_uri="${2:?repository URI required}"
image_digest="${3:?image digest required}"
previous_image_digest="${4-}"
legacy_release_id="${5-}"
health_host="${6:?health host required}"
container_unit_source="${7:?container unit source required}"
driver_asset_source="${8:?driver asset source required}"
release_action="${9:-release}"

case "$repository_uri" in
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].dkr.ecr.ap-northeast-1.amazonaws.com/co-story-tier3) ;;
  *) fail invalid_repository_uri; exit $? ;;
esac
[[ "$image_digest" =~ ^sha256:[a-f0-9]{64}$ ]] || { fail invalid_image_digest; exit $?; }
case "$health_host" in '' | *[!A-Za-z0-9.-]*) fail invalid_health_host; exit $? ;; esac
case "$test_root" in '' | /*) ;; *) fail invalid_test_root; exit $? ;; esac

readonly registry="${repository_uri%%/*}"
readonly target_image="$repository_uri@$image_digest"
readonly runtime_env="$(host_path /etc/co-story/runtime.env)"
readonly database_env="$(host_path /etc/co-story/database.env)"
readonly release_env="$(host_path /etc/co-story/container-release.env)"
readonly transition_state="$(host_path /etc/co-story/container-transition.state)"
readonly legacy_unit_backup="$(host_path /etc/co-story/legacy-co-story.service)"
readonly installed_unit="$(host_path /etc/systemd/system/co-story.service)"
readonly current_link="$(host_path /opt/co-story/current)"
readonly legacy_release="$(host_path "/opt/co-story/releases/$expected_legacy_release")"
readonly log_dir="$(host_path /var/log/co-story)"
readonly stable_driver="$(host_path /usr/local/libexec/co-story-deploy-container)"
readonly stable_container_unit="$(host_path /usr/local/share/co-story/co-story-container.service)"
readonly previous_driver_backup="$(host_path /etc/co-story/previous-stable-driver)"
readonly previous_unit_backup="$(host_path /etc/co-story/previous-stable-unit)"

case "$mode" in
  legacy-bootstrap) legacy_bootstrap ;;
  digest-release) digest_release ;;
  legacy-rollback) legacy_rollback ;;
  *) fail invalid_release_mode; exit $? ;;
esac
