#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
release_id="${1:?release id required}"
output_root="${2:-$ROOT/outputs/releases}"

case "$release_id" in
  *[!A-Za-z0-9._-]* | '')
    printf '%s\n' 'invalid release id' >&2
    exit 2
    ;;
esac

cd "$ROOT"
if [ -n "$(git status --porcelain)" ]; then
  printf '%s\n' 'working tree must be clean before building a release' >&2
  exit 2
fi

artifact_dir="$output_root/$release_id"
if [ -e "$artifact_dir" ]; then
  printf '%s\n' 'release artifact directory already exists' >&2
  exit 2
fi
mkdir -p "$artifact_dir"

archive="$artifact_dir/co-story.tar.gz"
temporary_tar="$artifact_dir/co-story.tar"
git archive --format=tar --prefix=co-story/ HEAD -o "$temporary_tar"
gzip -n "$temporary_tar"
install -m 0755 "$ROOT/ops/release/install_staging.sh" "$artifact_dir/install_staging.sh"

checksum="$(shasum -a 256 "$archive" | awk '{print $1}')"
printf '%s  %s\n' "$checksum" "$(basename "$archive")" > "$artifact_dir/co-story.tar.gz.sha256"
printf 'release_id=%s\ncommit=%s\n' "$release_id" "$(git rev-parse HEAD)" > "$artifact_dir/release-manifest.txt"

printf '%s\n' "$artifact_dir"
