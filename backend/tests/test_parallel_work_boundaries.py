import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_branch_boundaries.py"
POLICY = ROOT / ".agents" / "work-boundaries.json"
GUIDE = ROOT / "docs" / "governance" / "parallel-branch-boundaries.md"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _check(branch: str, *paths: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(CHECKER), "--branch", branch]
    for path in paths:
        command.extend(("--path", path))
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)


def test_policy_defines_exact_parallel_branches_and_protects_integration_state() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    assert set(policy["branches"]) == {
        "codex/story-quality",
        "codex/tier3-delivery",
    }
    assert "docs/handoffs/CURRENT.md" in policy["protected_paths"]
    assert "docs/checkpoints.md" in policy["protected_paths"]
    assert "docs/deployment-log.md" in policy["protected_paths"]
    assert ".agents/work-boundaries.json" in policy["protected_paths"]


def test_story_quality_branch_accepts_product_paths_and_rejects_delivery_paths() -> None:
    accepted = _check(
        "codex/story-quality",
        "backend/app/adapters/bedrock_storyteller.py",
        "backend/app/adapters/mock_storyteller.py",
        "backend/tests/test_story_narrative.py",
        "web/src/ui/pages/game-page.js",
        "docs/features/story-quality.md",
    )
    rejected = _check(
        "codex/story-quality",
        ".github/workflows/deploy.yml",
        "infra/cloudformation/tier3-delivery.yaml",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert ".github/workflows/deploy.yml" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier3_delivery_branch_accepts_delivery_paths_and_rejects_product_paths() -> None:
    accepted = _check(
        "codex/tier3-delivery",
        "Dockerfile",
        ".github/workflows/deploy.yml",
        "infra/cloudformation/tier3-delivery.yaml",
        "ops/release/container_activate.sh",
        "backend/tests/test_container_contract.py",
    )
    rejected = _check(
        "codex/tier3-delivery",
        "backend/co_story/domain/room.py",
        "web/src/ui/pages/game-page.js",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/co_story/domain/room.py" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_unknown_branch_fails_closed() -> None:
    result = _check("codex/unregistered-work", "README.md")

    assert result.returncode == 3
    assert "unregistered branch" in result.stderr


def test_governance_guide_and_pull_request_gate_are_present() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "codex/story-quality" in guide
    assert "codex/tier3-delivery" in guide
    assert "單一部署 owner" in guide
    assert "branch-boundary:" in workflow
    assert "scripts/check_branch_boundaries.py" in workflow
    assert "github.head_ref" in workflow
