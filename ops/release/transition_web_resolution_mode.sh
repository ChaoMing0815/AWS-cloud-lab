#!/usr/bin/env bash
set -euo pipefail

readonly expected_legacy_release=tier1-20260825-4a51e0e
readonly test_root="${CO_STORY_TEST_ROOT:-}"

fail() {
  printf 'web_mode_transition=stopped reason=%s\n' "${1:?reason required}" >&2
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

file_sha256() {
  path="${1:?file required}"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
  else
    shasum -a 256 "$path" | awk '{print $1}'
  fi
}

file_metadata() {
  kind="${1:?metadata kind required}"
  path="${2:?metadata path required}"
  if [ -n "$test_root" ]; then
    case "$kind" in
      installed-unit | stable-unit) printf '%s\n' 'root:root:644' ;;
      driver) printf '%s\n' 'root:root:755' ;;
      state | release | backup) printf '%s\n' 'root:root:600' ;;
      *) fail invalid_metadata_kind ;;
    esac
  else
    stat -c '%U:%G:%a' "$path"
  fi
}

validate_regular_file() {
  path="${1:?path required}"
  kind="${2:?kind required}"
  expected_metadata="${3:?metadata required}"
  [ -f "$path" ] || fail "missing_$kind"
  [ ! -L "$path" ] || fail "${kind}_must_not_be_symlink"
  if [ -z "$test_root" ]; then
    [ "$(readlink -f "$path" 2>/dev/null || true)" = "$path" ] \
      || fail "invalid_${kind}_path"
  fi
  [ "$(file_metadata "$kind" "$path")" = "$expected_metadata" ] \
    || fail "invalid_${kind}_metadata"
}

atomic_install() {
  source="${1:?source required}"
  destination="${2:?destination required}"
  mode="${3:?mode required}"
  directory="$(dirname "$destination")"
  temporary="$(mktemp "$directory/.co-story-web-mode.XXXXXX")"
  if ! install -m "$mode" "$source" "$temporary"; then
    rm -f "$temporary"
    return 1
  fi
  if [ -z "$test_root" ] && ! chown root:root "$temporary"; then
    rm -f "$temporary"
    return 1
  fi
  if ! mv -f "$temporary" "$destination"; then
    rm -f "$temporary"
    return 1
  fi
}

atomic_write() {
  destination="${1:?destination required}"
  mode="${2:?mode required}"
  content="${3-}"
  directory="$(dirname "$destination")"
  temporary="$(mktemp "$directory/.co-story-web-mode-state.XXXXXX")"
  if ! printf '%s' "$content" >"$temporary" || ! chmod "$mode" "$temporary"; then
    rm -f "$temporary"
    return 1
  fi
  if [ -z "$test_root" ] && ! chown root:root "$temporary"; then
    rm -f "$temporary"
    return 1
  fi
  if ! mv -f "$temporary" "$destination"; then
    rm -f "$temporary"
    return 1
  fi
}

state_value() {
  key="${1:?state key required}"
  value="$(awk -F= -v key="$key" '$1 == key {print substr($0, length(key) + 2)}' "$transition_state")"
  count="$(awk -F= -v key="$key" '$1 == key {count++} END {print count + 0}' "$transition_state")"
  [ "$count" -eq 1 ] || fail duplicate_or_missing_state_key
  printf '%s\n' "$value"
}

release_value() {
  key="${1:?release key required}"
  value="$(awk -F= -v key="$key" '$1 == key {print substr($0, length(key) + 2)}' "$release_env")"
  count="$(awk -F= -v key="$key" '$1 == key {count++} END {print count + 0}' "$release_env")"
  [ "$count" -eq 1 ] || fail duplicate_or_missing_release_key
  printf '%s\n' "$value"
}

write_state() {
  status="${1:?status required}"
  unit_sha="${2:?unit checksum required}"
  atomic_write "$transition_state" 0600 "STATE=$status
LEGACY_RELEASE_ID=$state_legacy_id
LEGACY_RELEASE_TARGET=$state_legacy_target
LEGACY_UNIT_SHA256=$state_legacy_unit_sha
DRIVER_SHA256=$state_driver_sha
CONTAINER_UNIT_SHA256=$unit_sha
CONTAINER_IMAGE=$state_image
"
}

validate_unit_mode() {
  path="${1:?unit path required}"
  expected_mode="${2:?expected mode required}"
  mode_count="$(awk -v expected="Environment=CO_STORY_RESOLUTION_MODE=$expected_mode" \
    '$0 == expected {count++} END {print count + 0}' "$path")"
  source_count="$(awk '/^Environment=CO_STORY_RESOLUTION_MODE=/ {count++} END {print count + 0}' "$path")"
  propagation_count="$(awk '{line=$0; while (match(line, /--env CO_STORY_RESOLUTION_MODE=\$\{CO_STORY_RESOLUTION_MODE\}/)) {count++; line=substr(line, RSTART + RLENGTH)}} END {print count + 0}' "$path")"
  [ "$mode_count" -eq 1 ] && [ "$source_count" -eq 1 ] \
    || fail invalid_unit_mode_source
  [ "$propagation_count" -eq 1 ] || fail invalid_unit_mode_propagation
}

make_target_unit() {
  source="${1:?source unit required}"
  destination="${2:?target unit required}"
  from="${3:?current mode required}"
  to="${4:?target mode required}"
  if ! awk -v from="Environment=CO_STORY_RESOLUTION_MODE=$from" \
    -v to="Environment=CO_STORY_RESOLUTION_MODE=$to" '
      $0 == from {print to; count++; next}
      {print}
      END {if (count != 1) exit 2}
    ' "$source" >"$destination"; then
    rm -f "$destination"
    return 1
  fi
  chmod 0600 "$destination"
}

wait_for_health() {
  label="${1:?health label required}"
  expected_mode="${2:?mode required}"
  record_event "health:$label:$expected_mode"
  health_failure_reason="${label}_unknown_health_failed"
  if failure_enabled "${label}-health"; then
    health_failure_reason="${label}_health_failed"
    return 1
  fi
  for phase in service-active container-running restart-count image mode \
    internal-live internal-ready public-live public-ready; do
    if failure_enabled "${label}-${phase}"; then
      normalized_phase="${phase//-/_}"
      health_failure_reason="${label}_${normalized_phase}_failed"
      return 1
    fi
  done
  if [ -n "$test_root" ]; then
    if [ "${CO_STORY_TEST_SERVICE_STATE:-inactive}" != active ]; then
      health_failure_reason="${label}_service_active_failed"
      return 1
    fi
    if [ "${CO_STORY_TEST_CONTAINER_STATE:-absent}" != running ]; then
      health_failure_reason="${label}_container_running_failed"
      return 1
    fi
    if [ "${CO_STORY_TEST_CONTAINER_RESTARTS:-unknown}" != 0 ]; then
      health_failure_reason="${label}_restart_count_failed"
      return 1
    fi
    if [ "$test_container_mode" != "$expected_mode" ]; then
      health_failure_reason="${label}_mode_failed"
      return 1
    fi
    return 0
  fi
  if ! systemctl is-active --quiet co-story.service; then
    health_failure_reason="${label}_service_active_failed"
    return 1
  fi
  if [ "$(docker inspect --format '{{.State.Status}}' co-story 2>/dev/null || true)" != running ]; then
    health_failure_reason="${label}_container_running_failed"
    return 1
  fi
  if [ "$(docker inspect --format '{{.RestartCount}}' co-story 2>/dev/null || true)" != 0 ]; then
    health_failure_reason="${label}_restart_count_failed"
    return 1
  fi
  if [ "$(docker inspect --format '{{.Config.Image}}' co-story 2>/dev/null || true)" != "$release_image" ]; then
    health_failure_reason="${label}_image_failed"
    return 1
  fi
  observed_mode="$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' co-story 2>/dev/null \
    | awk -F= '$1 == "CO_STORY_RESOLUTION_MODE" {count++; value=substr($0, length($1) + 2)} END {if (count == 1) print value}')"
  if [ "$observed_mode" != "$expected_mode" ]; then
    health_failure_reason="${label}_mode_failed"
    return 1
  fi
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if ! curl --fail --silent --max-time 3 \
      --header "Host: $health_host" http://127.0.0.1:8000/api/v1/live >/dev/null; then
      health_failure_reason="${label}_internal_live_failed"
    elif ! curl --fail --silent --max-time 3 \
      --header "Host: $health_host" http://127.0.0.1:8000/api/v1/ready >/dev/null; then
      health_failure_reason="${label}_internal_ready_failed"
    elif ! curl --fail --silent --max-time 3 \
      --resolve "$health_host:443:127.0.0.1" "https://$health_host/api/v1/live" >/dev/null; then
      health_failure_reason="${label}_public_live_failed"
    elif ! curl --fail --silent --max-time 3 \
      --resolve "$health_host:443:127.0.0.1" "https://$health_host/api/v1/ready" >/dev/null; then
      health_failure_reason="${label}_public_ready_failed"
    else
      return 0
    fi
    if [ "$attempt" -lt 30 ]; then sleep 1; fi
    attempt=$((attempt + 1))
  done
  return 1
}

restart_web() {
  label="${1:?restart label required}"
  mode="${2:?mode required}"
  record_event "service:$label"
  failure_enabled "$label" && return 1
  if [ -n "$test_root" ]; then
    test_container_mode="$mode"
    return 0
  fi
  systemctl restart co-story.service
}

cleanup_candidate() {
  if [ "${candidate_active:-no}" = yes ]; then
    if [ -z "$test_root" ]; then
      docker rm -f co-story-web-mode-candidate >/dev/null 2>&1 || true
    fi
    candidate_active=no
  fi
}

cleanup_ephemeral() {
  cleanup_candidate
  if [ -n "${target_unit:-}" ]; then rm -f "$target_unit"; fi
}

check_target_candidate() {
  record_event "candidate:$target_mode"
  failure_enabled target-candidate && return 1
  if [ -n "$test_root" ]; then return 0; fi
  if docker inspect co-story-web-mode-candidate >/dev/null 2>&1; then
    return 1
  fi
  candidate_active=yes
  if ! docker run --detach --name co-story-web-mode-candidate --network host \
    --read-only --cap-drop ALL --security-opt no-new-privileges \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --env-file /etc/co-story/runtime.env \
    --env-file /etc/co-story/database.env \
    --env CO_STORY_APPLICATION_LOG_PATH=/var/log/co-story/candidate.jsonl \
    --env CO_STORY_RESOLUTION_MODE=$target_mode \
    --mount type=bind,src=/etc/pki/rds/rds-ca.pem,dst=/etc/pki/rds/rds-ca.pem,readonly \
    --mount type=bind,src=/var/log/co-story,dst=/var/log/co-story \
    --user "$release_uid:$release_gid" \
    "$release_image" uvicorn app.main:create_app --factory \
    --host 127.0.0.1 --port 8001 --workers 1 >/dev/null 2>&1; then
    cleanup_candidate
    return 1
  fi
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if curl --fail --silent --max-time 3 \
      --header "Host: $health_host" http://127.0.0.1:8001/api/v1/live >/dev/null \
      && curl --fail --silent --max-time 3 \
        --header "Host: $health_host" http://127.0.0.1:8001/api/v1/ready >/dev/null; then
      cleanup_candidate
      return 0
    fi
    if [ "$attempt" -lt 30 ]; then sleep 1; fi
    attempt=$((attempt + 1))
  done
  candidate_state="$(docker inspect --format '{{.State.Status}} {{.State.ExitCode}}' \
    co-story-web-mode-candidate 2>/dev/null || true)"
  case "$candidate_state" in
    created\ [0-9]* | running\ [0-9]* | paused\ [0-9]* | restarting\ [0-9]* | \
      removing\ [0-9]* | exited\ [0-9]* | dead\ [0-9]*)
      printf 'web_mode_candidate=unhealthy status=%s exit_code=%s\n' \
        "${candidate_state% *}" "${candidate_state##* }" >&2
      ;;
    *) printf '%s\n' 'web_mode_candidate=unhealthy status=unknown exit_code=unknown' >&2 ;;
  esac
  cleanup_candidate
  return 1
}

cleanup_backups() {
  failure_enabled cleanup && return 1
  rm -f "$unit_backup" "$state_backup"
  [ ! -e "$unit_backup" ] && [ ! -e "$state_backup" ]
}

write_forensic_state() {
  write_state web-mode-restore-failed "$state_unit_sha" || true
}

restore_previous() {
  restored=yes
  restore_failure_reason=restore_unknown_failed
  record_event mutation:restore-units
  if failure_enabled restore-install \
    || ! atomic_install "$unit_backup" "$stable_unit" 0644 \
    || ! atomic_install "$unit_backup" "$installed_unit" 0644; then
    restored=no
    restore_failure_reason=restore_unit_install_failed
  fi
  if [ "$restored" = yes ]; then
    record_event service:restore-daemon-reload
    if failure_enabled restore-daemon-reload; then
      restored=no
      restore_failure_reason=restore_daemon_reload_failed
    elif [ -z "$test_root" ] && ! systemctl daemon-reload; then
      restored=no
      restore_failure_reason=restore_daemon_reload_failed
    fi
  fi
  if [ "$restored" = yes ] && ! restart_web restore-restart "$current_mode"; then
    restored=no
    restore_failure_reason=restore_restart_failed
  fi
  if [ "$restored" = yes ] && ! wait_for_health restore "$current_mode"; then
    restored=no
    restore_failure_reason="$health_failure_reason"
  fi
  if [ "$restored" = yes ] && ! atomic_install "$state_backup" "$transition_state" 0600; then
    restored=no
    restore_failure_reason=restore_state_install_failed
  fi
  if [ "$restored" = yes ] && cleanup_backups; then
    return 0
  fi
  if [ "$restored" = yes ]; then
    restore_failure_reason=restore_cleanup_failed
  fi
  write_forensic_state
  return 1
}

transition_failed() {
  reason="${1:?reason required}"
  if restore_previous; then
    fail "$reason"
    return $?
  fi
  printf 'web_mode_transition=original-failure reason=%s\n' "$reason" >&2
  fail "$restore_failure_reason"
}

[ "$#" -eq 3 ] || { fail invalid_argument_count; exit $?; }
action="$1"
expected_digest="$2"
health_host="$3"
case "$action" in
  activate)
    readonly current_mode=sync
    readonly target_mode=async
    readonly success_message='web_async_activation=verified previous=sync current=async'
    ;;
  rollback)
    readonly current_mode=async
    readonly target_mode=sync
    readonly success_message='web_async_rollback=verified previous=async current=sync'
    ;;
  *) fail invalid_action; exit $? ;;
esac
[[ "$expected_digest" =~ ^sha256:[a-f0-9]{64}$ ]] \
  || { fail invalid_expected_digest; exit $?; }
case "$health_host" in '' | *[!A-Za-z0-9.-]*) fail invalid_health_host; exit $? ;; esac
if [ -z "$test_root" ] && [ "$(id -u)" -ne 0 ]; then
  fail must_run_as_root
  exit $?
fi

readonly installed_unit="$(host_path /etc/systemd/system/co-story.service)"
readonly stable_unit="$(host_path /usr/local/share/co-story/co-story-container.service)"
readonly stable_driver="$(host_path /usr/local/libexec/co-story-deploy-container)"
readonly transition_state="$(host_path /etc/co-story/container-transition.state)"
readonly release_env="$(host_path /etc/co-story/container-release.env)"
readonly unit_backup="$(host_path /etc/co-story/web-mode-previous-unit)"
readonly state_backup="$(host_path /etc/co-story/web-mode-previous-state)"
candidate_active=no
target_unit=
trap cleanup_ephemeral EXIT

[ ! -e "$unit_backup" ] && [ ! -e "$state_backup" ] \
  || { fail existing_web_mode_backup; exit $?; }
validate_regular_file "$installed_unit" installed-unit root:root:644
validate_regular_file "$stable_unit" stable-unit root:root:644
validate_regular_file "$stable_driver" driver root:root:755
validate_regular_file "$transition_state" state root:root:600
validate_regular_file "$release_env" release root:root:600
[ "$(wc -l <"$transition_state" | tr -d ' ')" -eq 7 ] \
  || { fail invalid_transition_state_shape; exit $?; }
[ "$(wc -l <"$release_env" | tr -d ' ')" -eq 3 ] \
  || { fail invalid_release_env_shape; exit $?; }

state_status="$(state_value STATE)"
state_legacy_id="$(state_value LEGACY_RELEASE_ID)"
state_legacy_target="$(state_value LEGACY_RELEASE_TARGET)"
state_legacy_unit_sha="$(state_value LEGACY_UNIT_SHA256)"
state_driver_sha="$(state_value DRIVER_SHA256)"
state_unit_sha="$(state_value CONTAINER_UNIT_SHA256)"
state_image="$(state_value CONTAINER_IMAGE)"
[ "$state_status" = container-active ] || { fail container_state_not_active; exit $?; }
[ "$state_legacy_id" = "$expected_legacy_release" ] \
  || { fail legacy_state_mismatch; exit $?; }
[ "$state_legacy_target" = "/opt/co-story/releases/$expected_legacy_release" ] \
  || { fail legacy_target_mismatch; exit $?; }
for checksum in "$state_legacy_unit_sha" "$state_driver_sha" "$state_unit_sha"; do
  [[ "$checksum" =~ ^[a-f0-9]{64}$ ]] || { fail invalid_state_checksum; exit $?; }
done
[[ "$state_image" =~ ^[0-9]{12}\.dkr\.ecr\.ap-northeast-1\.amazonaws\.com/co-story-tier3@${expected_digest}$ ]] \
  || { fail active_digest_state_mismatch; exit $?; }

release_image="$(release_value CO_STORY_CONTAINER_IMAGE)"
release_uid="$(release_value CO_STORY_CONTAINER_UID)"
release_gid="$(release_value CO_STORY_CONTAINER_GID)"
[[ "$release_uid" =~ ^[1-9][0-9]*$ ]] && [[ "$release_gid" =~ ^[1-9][0-9]*$ ]] \
  || { fail invalid_release_identity; exit $?; }
[ "$release_image" = "$state_image" ] || { fail release_state_image_mismatch; exit $?; }
[ "$(file_sha256 "$stable_driver")" = "$state_driver_sha" ] \
  || { fail stable_driver_checksum_mismatch; exit $?; }
[ "$(file_sha256 "$stable_unit")" = "$state_unit_sha" ] \
  || { fail stable_unit_checksum_mismatch; exit $?; }
[ "$(file_sha256 "$installed_unit")" = "$state_unit_sha" ] \
  || { fail installed_unit_checksum_mismatch; exit $?; }
cmp -s "$stable_unit" "$installed_unit" \
  || { fail installed_stable_unit_mismatch; exit $?; }
validate_unit_mode "$stable_unit" "$current_mode"

test_container_mode="${CO_STORY_TEST_CONTAINER_MODE:-unknown}"
if ! wait_for_health preflight "$current_mode"; then
  fail "$health_failure_reason"
  exit $?
fi

target_unit="$(mktemp "$(dirname "$stable_unit")/.co-story-web-mode-target.XXXXXX")"
make_target_unit "$stable_unit" "$target_unit" "$current_mode" "$target_mode" \
  || { fail target_unit_build_failed; exit $?; }
validate_unit_mode "$target_unit" "$target_mode"
target_unit_sha="$(file_sha256 "$target_unit")"
check_target_candidate || { fail target_candidate_failed; exit $?; }

atomic_install "$stable_unit" "$unit_backup" 0600 \
  || { fail unit_backup_failed; exit $?; }
atomic_install "$transition_state" "$state_backup" 0600 \
  || { rm -f "$unit_backup"; fail state_backup_failed; exit $?; }
record_event mutation:pending-state
write_state web-mode-switch-pending "$state_unit_sha" \
  || transition_failed pending_state_write_failed
record_event mutation:stable-unit
if failure_enabled stable-unit-install \
  || ! atomic_install "$target_unit" "$stable_unit" 0644; then
  transition_failed stable_unit_install_failed
fi
record_event mutation:installed-unit
if failure_enabled installed-unit-install \
  || ! atomic_install "$target_unit" "$installed_unit" 0644; then
  transition_failed installed_unit_install_failed
fi
if failure_enabled target-unit-drift; then
  printf '%s\n' '# injected target unit drift' >>"$installed_unit"
fi
if [ "$(file_sha256 "$stable_unit")" != "$target_unit_sha" ] \
  || [ "$(file_sha256 "$installed_unit")" != "$target_unit_sha" ]; then
  transition_failed target_unit_checksum_mismatch
fi
record_event service:target-daemon-reload
if failure_enabled target-daemon-reload; then
  transition_failed target_daemon_reload_failed
elif [ -z "$test_root" ] && ! systemctl daemon-reload; then
  transition_failed target_daemon_reload_failed
fi
restart_web target-restart "$target_mode" || transition_failed target_restart_failed
if ! wait_for_health target "$target_mode"; then
  transition_failed "$health_failure_reason"
fi
record_event mutation:final-state
if failure_enabled final-state || ! write_state container-active "$target_unit_sha"; then
  transition_failed final_state_write_failed
fi
if ! cleanup_backups; then
  write_state web-mode-cleanup-failed "$target_unit_sha" || true
  fail backup_cleanup_failed
  exit $?
fi
printf '%s\n' "$success_message"
