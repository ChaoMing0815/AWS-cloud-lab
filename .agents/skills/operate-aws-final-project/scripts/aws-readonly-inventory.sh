#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'Usage: aws-readonly-inventory.sh --profile PROFILE --region REGION --output-dir DIR [--cost-start YYYY-MM-DD --cost-end YYYY-MM-DD]' \
    '' \
    'Runs read-only AWS inventory commands and writes JSON evidence. It never exports credentials or secret values.'
}

profile=''
region=''
output_dir=''
cost_start=''
cost_end=''

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) profile="${2:-}"; shift 2 ;;
    --region) region="${2:-}"; shift 2 ;;
    --output-dir) output_dir="${2:-}"; shift 2 ;;
    --cost-start) cost_start="${2:-}"; shift 2 ;;
    --cost-end) cost_end="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$profile" || -z "$region" || -z "$output_dir" ]]; then
  usage >&2
  exit 2
fi

mkdir -p "$output_dir"

aws_cli=(aws --profile "$profile" --region "$region" --no-cli-pager --output json)
failures=0

run_json() {
  local filename="$1"
  shift
  if ! "$@" > "$output_dir/$filename" 2> "$output_dir/${filename%.json}.stderr.txt"; then
    failures=$((failures + 1))
  fi
}

run_json sts-caller-identity.json "${aws_cli[@]}" sts get-caller-identity
account_id="$("${aws_cli[@]}" sts get-caller-identity --query Account --output text)"
run_json iam-account-summary.json "${aws_cli[@]}" iam get-account-summary
run_json iam-users.json "${aws_cli[@]}" iam list-users
run_json iam-groups.json "${aws_cli[@]}" iam list-groups
run_json iam-roles.json "${aws_cli[@]}" iam list-roles
run_json iam-customer-managed-policies.json "${aws_cli[@]}" iam list-policies --scope Local
run_json identity-center-instances.json "${aws_cli[@]}" sso-admin list-instances
run_json budgets.json "${aws_cli[@]}" budgets describe-budgets --account-id "$account_id"
run_json cloudtrail-trails.json "${aws_cli[@]}" cloudtrail describe-trails
run_json cloudtrail-recent-events.json "${aws_cli[@]}" cloudtrail lookup-events --max-results 10

run_json tagged-resources.json "${aws_cli[@]}" resourcegroupstaggingapi get-resources
run_json ec2-instances.json "${aws_cli[@]}" ec2 describe-instances
run_json ec2-vpcs.json "${aws_cli[@]}" ec2 describe-vpcs
run_json ec2-subnets.json "${aws_cli[@]}" ec2 describe-subnets
run_json ec2-security-groups.json "${aws_cli[@]}" ec2 describe-security-groups
run_json rds-db-instances.json "${aws_cli[@]}" rds describe-db-instances
run_json lambda-functions.json "${aws_cli[@]}" lambda list-functions
run_json ssm-managed-instances.json "${aws_cli[@]}" ssm describe-instance-information
run_json cloudwatch-alarms.json "${aws_cli[@]}" cloudwatch describe-alarms
run_json cloudwatch-log-groups.json "${aws_cli[@]}" logs describe-log-groups
run_json secrets-metadata.json "${aws_cli[@]}" secretsmanager list-secrets
run_json dynamodb-tables.json "${aws_cli[@]}" dynamodb list-tables
run_json s3-buckets.json "${aws_cli[@]}" s3api list-buckets

instance_arn="$("${aws_cli[@]}" sso-admin list-instances --query 'Instances[0].InstanceArn' --output text 2>/dev/null || true)"
identity_store_id="$("${aws_cli[@]}" sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text 2>/dev/null || true)"
if [[ -n "$instance_arn" && "$instance_arn" != 'None' ]]; then
  run_json identity-center-permission-sets.json "${aws_cli[@]}" sso-admin list-permission-sets --instance-arn "$instance_arn"
fi
if [[ -n "$identity_store_id" && "$identity_store_id" != 'None' ]]; then
  run_json identity-center-users.json "${aws_cli[@]}" identitystore list-users --identity-store-id "$identity_store_id"
  run_json identity-center-groups.json "${aws_cli[@]}" identitystore list-groups --identity-store-id "$identity_store_id"
fi

while IFS= read -r user_name; do
  [[ -z "$user_name" ]] && continue
  safe_user="${user_name//[^A-Za-z0-9+=,.@_-]/_}"
  run_json "iam-access-key-metadata-${safe_user}.json" "${aws_cli[@]}" iam list-access-keys \
    --user-name "$user_name" \
    --query 'AccessKeyMetadata[].{UserName:UserName,Status:Status,CreateDate:CreateDate}'
done < <("${aws_cli[@]}" iam list-users --query 'Users[].UserName' --output text | tr '\t' '\n')

if [[ -n "$cost_start" || -n "$cost_end" ]]; then
  if [[ -z "$cost_start" || -z "$cost_end" ]]; then
    printf '%s\n' 'Both --cost-start and --cost-end are required.' >&2
    exit 2
  fi
  run_json cost-explorer-unblended-cost.json "${aws_cli[@]}" ce get-cost-and-usage \
    --time-period "Start=${cost_start},End=${cost_end}" \
    --granularity MONTHLY \
    --metrics UnblendedCost
fi

printf 'Read-only AWS inventory saved to %s (%d command failures; inspect *.stderr.txt).\n' "$output_dir" "$failures"
