from pathlib import Path


ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/tier2-worker-image.yml"


def _workflow() -> str:
    assert WORKFLOW.is_file(), "Tier 2 Worker image workflow 尚未建立"
    return WORKFLOW.read_text(encoding="utf-8")


def test_worker_image_workflow_is_manual_approved_main_only_and_pushes_exact_arm64() -> None:
    workflow = _workflow()

    assert "workflow_dispatch:" in workflow
    assert "environment: production" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "needs: approval-gate" in workflow
    assert "id-token: write" in workflow
    assert "contents: read" in workflow
    assert "aws-actions/configure-aws-credentials@v5.1.0" in workflow
    assert "aws-actions/amazon-ecr-login@v2.0.1" in workflow
    assert "platforms: linux/arm64" in workflow
    assert "push: true" in workflow
    assert "${{ github.sha }}" in workflow
    assert "${{ steps.build.outputs.digest }}" in workflow


def test_worker_image_workflow_scans_digest_fail_closed_without_deploying() -> None:
    workflow = _workflow()

    assert "aquasecurity/trivy-action@v0.36.0" in workflow
    assert "TRIVY_PLATFORM: linux/arm64" in workflow
    assert "severity: CRITICAL,HIGH" in workflow
    assert "ignore-unfixed: true" in workflow
    assert "exit-code: 1" in workflow
    assert "tier2-worker-image-${{ github.run_id }}" in workflow
    assert "image_digest" in workflow
    assert "aws ssm" not in workflow
    assert "send-command" not in workflow
    assert "CoStoryTier3ContainerRelease" not in workflow
    assert "CO_STORY_RESOLUTION_MODE" not in workflow
