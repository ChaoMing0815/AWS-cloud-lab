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
    assert "\n  pull_request:" not in workflow
    assert "\n  push:" not in workflow
    assert "environment: production" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "approval-gate:" in workflow
    assert "deploy:" in workflow
    assert "needs: approval-gate" in workflow
    assert "id-token: write" in workflow
    assert "contents: read" in workflow
    assert "aws-actions/configure-aws-credentials@" in workflow
    assert "docker/setup-qemu-action@" in workflow
    assert "platforms: linux/arm64" in workflow
    assert "role-to-assume: ${{ vars.TIER3_DEPLOY_ROLE_ARN }}" in workflow
    assert "aws-region: ${{ vars.AWS_REGION }}" in workflow
    assert "aws ssm send-command" in workflow
    assert "aws ssm wait command-executed" in workflow
    assert "aws ssm get-command-invocation" in workflow
    assert "--document-name CoStoryTier3ContainerRelease" in workflow
    assert "image_digest" in workflow
    assert "previous_image_digest" in workflow
    assert ":latest" not in workflow
    assert "secrets." not in workflow
    assert "aws-access-key-id" not in workflow
    assert "aws-secret-access-key" not in workflow


def test_release_workflow_distinguishes_legacy_bootstrap_from_digest_release() -> None:
    workflow = _read(RELEASE_WORKFLOW)

    assert "release_mode:" in workflow
    assert "legacy-bootstrap" in workflow
    assert "digest-release" in workflow
    assert "expected_legacy_release" in workflow
    assert "tier1-20260825-4a51e0e" in workflow
    assert "bootstrap must not provide a previous digest" in workflow
    assert "digest release requires a previous digest" in workflow
    assert "target and previous image digests must differ" in workflow
    scan_at = workflow.index("Scan the exact pushed digest")
    release_at = workflow.index("Release exact digest through bounded SSM document")
    assert scan_at < release_at
    assert "ReleaseMode" in workflow
    assert "ExpectedLegacyRelease" in workflow


def test_cloudformation_limits_oidc_ecr_and_ssm_to_repo_branch_and_instance() -> None:
    template_text = _read(TEMPLATE)
    template = yaml.safe_load(template_text)
    resources = template["Resources"]

    assert "Tier3Repository" in resources
    assert resources["Tier3Repository"]["Properties"]["ImageScanningConfiguration"]["ScanOnPush"] is True
    assert resources["Tier3Repository"]["Properties"]["ImageTagMutability"] == "IMMUTABLE"
    assert "GitHubDeployRole" in resources
    assert resources["GitHubDeployRole"]["Properties"]["PermissionsBoundary"] == {
        "Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/PowerUserAccess"
    }
    assert "token.actions.githubusercontent.com:aud" in template_text
    assert "sts.amazonaws.com" in template_text
    assert "repo:ChaoMing0815/AWS-cloud-lab:ref:refs/heads/main" in template_text
    assert "ecr:GetAuthorizationToken" in template_text
    assert "ecr:PutImage" in template_text
    assert "AppEcrPullPolicy" in template_text
    assert "ecr:BatchGetImage" in template_text
    assert "ecr:GetDownloadUrlForLayer" in template_text
    assert "ssm:SendCommand" in template_text
    assert "AWS::EC2::Instance" in template_text
    assert "arn:${AWS::Partition}:ssm:${AWS::Region}:${AWS::AccountId}:document/CoStoryTier3ContainerRelease" in template_text
    assert "iam:PassRole" not in template_text
    assert "AdministratorAccess" not in template_text
    assert template_text.count("Resource: '*'") == 3


def test_ssm_release_document_and_host_script_fail_closed_with_rollback() -> None:
    template = _read(TEMPLATE)
    script = _read(RELEASE_SCRIPT)

    assert "CoStoryTier3ContainerRelease" in template
    assert "ImageDigest" in template
    assert "PreviousImageDigest" in template
    assert "allowedPattern: '^sha256:[a-f0-9]{64}$'" in template
    assert "deploy_container.sh" in template
    assert "set -euo pipefail" in script
    assert "docker pull" in script
    assert "aws ecr get-login-password" in script
    assert "--password-stdin" in script
    assert "app.commands.migrate" in script
    assert "/api/v1/live" in script
    assert "/api/v1/ready" in script
    assert "candidate" in script
    assert "previous_image_digest" in script
    assert '"$image_digest" = "$previous_image_digest"' in script
    assert "restore_previous" in script
    assert "systemctl restart co-story.service" in script
    assert "DATABASE_URL" not in script
    assert "set -x" not in script
    assert "--privileged" not in script


def test_ssm_documents_bound_bootstrap_assets_and_keep_legacy_rollback_human_only() -> None:
    template_text = _read(TEMPLATE)
    template = yaml.safe_load(template_text)
    resources = template["Resources"]
    deploy_policy = resources["GitHubDeployRole"]["Properties"]["Policies"][0][
        "PolicyDocument"
    ]["Statement"]
    send_command = next(
        statement
        for statement in deploy_policy
        if statement["Sid"] == "ReleaseOnlyThroughPinnedDocumentAndInstance"
    )

    assert "LegacyRollbackDocument" in resources
    assert resources["LegacyRollbackDocument"]["Properties"]["Name"] == (
        "CoStoryTier3LegacyRollback"
    )
    assert "CoStoryTier3LegacyRollback" not in str(send_command["Resource"])
    assert "ReleaseMode" in template_text
    assert "legacy-bootstrap" in template_text
    bootstrap = template_text.index("legacy-bootstrap)")
    first_pull = template_text.index('docker pull "$target_image"', bootstrap)
    for preflight_guard in (
        'readlink -f /opt/co-story/current',
        'stat -c \'%U:%G:%a\' "$runtime_env"',
        'test ! -e /etc/co-story/container-transition.state',
        'test ! -e /etc/co-story/container-release.env',
        'cmp -s /etc/systemd/system/co-story.service',
        'legacy_preflight',
    ):
        assert bootstrap < template_text.index(preflight_guard, bootstrap) < first_pull
    assert "digest-release" in template_text
    assert "tier1-20260825-4a51e0e" in template_text
    assert "/usr/local/share/co-story/deploy_container.sh" in template_text
    assert "/usr/local/share/co-story/co-story-container.service" in template_text
    assert "/usr/local/libexec/co-story-deploy-container" in template_text
    assert "docker create" in template_text
    assert "docker cp" in template_text
    digest = template_text.index("digest-release)")
    rollback = template_text.index("LegacyRollbackDocument:")
    digest_block = template_text[digest:rollback]
    assert 'docker pull "$target_image"' in digest_block
    assert 'docker create --name "$asset_container" "$target_image"' in digest_block
    assert 'docker cp "$asset_container:/usr/local/share/co-story/deploy_container.sh"' in digest_block
    assert 'docker cp "$asset_container:/usr/local/share/co-story/co-story-container.service"' in digest_block
    assert '"$temporary/deploy_container.sh"' in digest_block
    assert '"$temporary/co-story-container.service"' in digest_block
    assert "curl --location" not in template_text
    assert "curl -L" not in template_text
    assert "https://raw." not in template_text
    assert "wget " not in template_text
    assert "aws s3" not in template_text.lower()
