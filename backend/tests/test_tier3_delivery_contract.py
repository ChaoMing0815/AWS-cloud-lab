from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
RELEASE_WORKFLOW = ROOT / ".github/workflows/tier3-release.yml"
TEMPLATE = ROOT / "infra/cloudformation/tier3-delivery.yaml"
RELEASE_SCRIPT = ROOT / "ops/release/deploy_container.sh"


def _read(path: Path) -> str:
    assert path.is_file(), f"Tier 3 asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_release_workflow_is_manual_approved_main_only_and_digest_pinned() -> None:
    workflow = _read(RELEASE_WORKFLOW)

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "environment: production" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "approval-gate:" in workflow
    assert "deploy:" in workflow
    assert "needs: approval-gate" in workflow
    assert "id-token: write" in workflow
    assert "contents: read" in workflow
    assert "aws-actions/configure-aws-credentials@" in workflow
    assert "role-to-assume: ${{ vars.TIER3_DEPLOY_ROLE_ARN }}" in workflow
    assert "aws-region: ${{ vars.AWS_REGION }}" in workflow
    assert "aws ssm send-command" in workflow
    assert "--document-name CoStoryTier3ContainerRelease" in workflow
    assert "image_digest" in workflow
    assert "previous_image_digest" in workflow
    assert ":latest" not in workflow
    assert "secrets." not in workflow
    assert "aws-access-key-id" not in workflow
    assert "aws-secret-access-key" not in workflow


def test_cloudformation_limits_oidc_ecr_and_ssm_to_repo_branch_and_instance() -> None:
    template_text = _read(TEMPLATE)
    template = yaml.safe_load(template_text)
    resources = template["Resources"]

    assert "Tier3Repository" in resources
    assert resources["Tier3Repository"]["Properties"]["ImageScanningConfiguration"]["ScanOnPush"] is True
    assert resources["Tier3Repository"]["Properties"]["ImageTagMutability"] == "IMMUTABLE"
    assert "GitHubDeployRole" in resources
    assert "token.actions.githubusercontent.com:aud" in template_text
    assert "sts.amazonaws.com" in template_text
    assert "repo:ChaoMing0815/AWS-cloud-lab:ref:refs/heads/main" in template_text
    assert "ecr:GetAuthorizationToken" in template_text
    assert "ecr:PutImage" in template_text
    assert "ssm:SendCommand" in template_text
    assert "AWS::EC2::Instance" in template_text
    assert "arn:${AWS::Partition}:ssm:${AWS::Region}::document/CoStoryTier3ContainerRelease" in template_text
    assert "iam:PassRole" not in template_text
    assert "AdministratorAccess" not in template_text
    assert template_text.count("Resource: '*'") == 1


def test_ssm_release_document_and_host_script_fail_closed_with_rollback() -> None:
    template = _read(TEMPLATE)
    script = _read(RELEASE_SCRIPT)

    assert "CoStoryTier3ContainerRelease" in template
    assert "ImageDigest" in template
    assert "PreviousImageDigest" in template
    assert "AllowedPattern: '^sha256:[a-f0-9]{64}$'" in template
    assert "deploy_container.sh" in template
    assert "set -euo pipefail" in script
    assert "docker pull" in script
    assert "app.commands.migrate" in script
    assert "/api/v1/live" in script
    assert "/api/v1/ready" in script
    assert "candidate" in script
    assert "previous_image_digest" in script
    assert "restore_previous" in script
    assert "systemctl restart co-story.service" in script
    assert "DATABASE_URL" not in script
    assert "set -x" not in script
    assert "--privileged" not in script
