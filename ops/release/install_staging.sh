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

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'installer must run as root' >&2
  exit 2
fi

release_id="${1:?release id required}"
db_endpoint="${2:?database endpoint required}"
master_secret_arn="${3:?master secret ARN required}"
app_secret_arn="${4:?application secret ARN required}"

case "$release_id" in
  *[!A-Za-z0-9._-]* | '')
    printf '%s\n' 'invalid release id' >&2
    exit 2
    ;;
esac
case "$db_endpoint" in
  *[!A-Za-z0-9.-]* | '')
    printf '%s\n' 'invalid database endpoint' >&2
    exit 2
    ;;
esac
case "$master_secret_arn" in
  arn:aws:secretsmanager:ap-northeast-1:*:secret:*) ;;
  *) printf '%s\n' 'invalid master secret ARN' >&2; exit 2 ;;
esac
case "$app_secret_arn" in
  arn:aws:secretsmanager:ap-northeast-1:*:secret:*) ;;
  *) printf '%s\n' 'invalid application secret ARN' >&2; exit 2 ;;
esac

artifact_root="$(pwd)"
archive="$artifact_root/co-story.tar.gz"
checksum_file="$artifact_root/co-story.tar.gz.sha256"
test -f "$archive"
test -f "$checksum_file"
sha256sum -c "$checksum_file"

root=/opt/co-story
releases="$root/releases"
release_dir="$releases/$release_id"
if [ -e "$release_dir" ]; then
  printf '%s\n' 'release directory already exists' >&2
  exit 2
fi
install -d -m 0755 "$releases"
resolved_releases="$(realpath -e "$releases")"
stage="$(mktemp -d "$root/.stage.$release_id.XXXXXX")"
success=0
previous_target=""
if [ -L "$root/current" ]; then
  previous_candidate="$(readlink -f "$root/current" 2>/dev/null || true)"
  case "$previous_candidate" in
    "$resolved_releases"/*)
      if [ -d "$previous_candidate" ]; then
        previous_target="$previous_candidate"
      fi
      ;;
  esac
fi

cleanup() {
  rm -rf "$stage"
  if [ "$success" -eq 0 ]; then
    active_target="$(readlink -f "$root/current" 2>/dev/null || true)"
    if [ -L "$root/current" ] && [ -z "$active_target" ]; then
      rm -f "$root/current"
      systemctl stop co-story-nginx-staging.service || true
      systemctl stop co-story.service || true
    fi
    if [ "$active_target" = "$release_dir" ]; then
      if [ -n "$previous_target" ]; then
        restore_link="$root/.current.install-restore.$release_id"
        rm -f "$restore_link"
        ln -s "$previous_target" "$restore_link"
        mv -Tf "$restore_link" "$root/current"
        systemctl restart co-story.service || true
        systemctl restart co-story-nginx-staging.service || true
      else
        rm -f "$root/current"
        systemctl stop co-story-nginx-staging.service || true
        systemctl stop co-story.service || true
      fi
    fi
    active_target="$(readlink -f "$root/current" 2>/dev/null || true)"
    if [ -d "$release_dir" ] && [ "$active_target" != "$release_dir" ]; then
      rm -rf "$release_dir"
    fi
  fi
}
trap cleanup EXIT

tar -xzf "$archive" -C "$stage"
test -d "$stage/co-story/backend"
mv "$stage/co-story" "$release_dir"

dnf install -y python3.13 python3.13-pip nginx
if ! getent group co-story >/dev/null; then
  groupadd --system co-story
fi
if ! id co-story >/dev/null 2>&1; then
  useradd --system --gid co-story --home-dir /nonexistent --shell /sbin/nologin co-story
fi

python3.13 -m venv "$release_dir/.venv"
"$release_dir/.venv/bin/python" -m pip install --no-deps --requirement "$release_dir/backend/requirements-prod.txt"

install -d -m 0750 -o root -g co-story /etc/co-story
runtime_tmp="$(mktemp /etc/co-story/.runtime.env.XXXXXX)"
printf '%s\n' \
  'CO_STORY_ENV=staging' \
  'CO_STORY_COOKIE_SECURE=false' \
  'CO_STORY_AWS_REGION=ap-northeast-1' > "$runtime_tmp"
chown root:co-story "$runtime_tmp"
chmod 0640 "$runtime_tmp"
mv -f "$runtime_tmp" /etc/co-story/runtime.env

install -d -m 0755 /etc/pki/rds
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
  --output /etc/pki/rds/rds-ca.pem
chmod 0644 /etc/pki/rds/rds-ca.pem

install -m 0644 "$release_dir/ops/systemd/co-story.service" /etc/systemd/system/co-story.service
install -m 0644 "$release_dir/ops/systemd/co-story-candidate@.service" /etc/systemd/system/co-story-candidate@.service
install -m 0644 "$release_dir/ops/systemd/co-story-migrate@.service" /etc/systemd/system/co-story-migrate@.service
install -m 0644 "$release_dir/ops/systemd/co-story-nginx-staging.service" /etc/systemd/system/co-story-nginx-staging.service
install -m 0644 "$release_dir/ops/nginx/co-story-staging.conf" /etc/nginx/co-story-staging.conf
systemctl daemon-reload

CO_STORY_AWS_REGION=ap-northeast-1 \
CO_STORY_DB_ENDPOINT="$db_endpoint" \
CO_STORY_DB_PORT=5432 \
CO_STORY_MASTER_SECRET_ARN="$master_secret_arn" \
CO_STORY_APP_DB_SECRET_ARN="$app_secret_arn" \
CO_STORY_RDS_CA_PATH=/etc/pki/rds/rds-ca.pem \
  "$release_dir/.venv/bin/python" "$release_dir/ops/runtime/bootstrap_database.py"

"$release_dir/ops/release/activate.sh" "$release_id" localhost
systemctl enable co-story.service
systemctl disable --now nginx.service >/dev/null 2>&1 || true
nginx -t -c /etc/nginx/co-story-staging.conf
systemctl enable --now co-story-nginx-staging.service
wait_for_readiness http://127.0.0.1:8080/api/v1/ready localhost

success=1
printf '%s\n' 'staging release installed'
