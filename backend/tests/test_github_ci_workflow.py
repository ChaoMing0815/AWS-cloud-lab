from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "tier3-release.yml"


def _workflow_text() -> str:
    assert WORKFLOW.is_file(), "GitHub CI workflow must exist"
    return WORKFLOW.read_text(encoding="utf-8")


def _release_workflow_text() -> str:
    assert RELEASE_WORKFLOW.is_file(), "GitHub release workflow must exist"
    return RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_ci_runs_backend_and_frontend_regressions_for_pull_requests() -> None:
    workflow = _workflow_text()

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "backend-tests:" in workflow
    assert "python-version: \"3.13\"" in workflow
    assert "python -m pip install --disable-pip-version-check -r backend/requirements-dev.txt" in workflow
    assert "python -m pytest -q backend/tests" in workflow
    assert "frontend-tests:" in workflow
    assert "node-version: \"24\"" in workflow
    assert "npm test" in workflow


def test_ci_is_read_only_and_builds_and_scans_only_after_test_gates() -> None:
    workflow = _workflow_text()

    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "id-token:" not in workflow
    assert "aws-actions/" not in workflow
    assert "amazon-ecr" not in workflow.lower()
    assert "deploy" not in workflow.lower()
    assert "container-build-scan:" in workflow
    assert "needs: [backend-tests, frontend-tests]" in workflow
    assert "docker/build-push-action@" in workflow
    assert "push: false" in workflow
    assert "aquasecurity/trivy-action@" in workflow
    assert "severity: CRITICAL,HIGH" in workflow
    assert "exit-code: 1" in workflow


def test_tier3_workflows_pin_trivy_to_the_resolvable_exact_release_tag() -> None:
    for workflow in (_workflow_text(), _release_workflow_text()):
        assert "aquasecurity/trivy-action@v0.33.1" in workflow
        assert "aquasecurity/trivy-action@0.33.1" not in workflow
