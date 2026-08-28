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
        "codex/tier3-production-release",
        "codex/tier3-healthcheck-correction",
        "codex/tier2-components",
        "codex/tier2-async-flow",
        "codex/tier2-migration-bridge",
        "codex/tier2-production-worker",
        "codex/support-agent-core",
        "codex/support-agent-durability",
        "codex/support-agent-persistence",
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


def test_tier3_production_release_accepts_release_paths_and_rejects_product_paths() -> None:
    accepted = _check(
        "codex/tier3-production-release",
        ".github/workflows/tier3-release.yml",
        "ops/release/deploy_container.sh",
        "backend/tests/test_github_ci_workflow.py",
        "docs/evidence/2026-08-26-tier3-production-release/validation.md",
    )
    rejected = _check(
        "codex/tier3-production-release",
        "backend/app/application/story_jobs.py",
        "web/src/ui/pages/game-page.js",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/application/story_jobs.py" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier3_healthcheck_correction_accepts_only_the_approved_slice() -> None:
    accepted = _check(
        "codex/tier3-healthcheck-correction",
        "Dockerfile",
        "ops/container/healthcheck.py",
        "backend/tests/test_container_contract.py",
        "docs/evidence/2026-08-27-tier3-production-release/validation.md",
    )
    rejected = _check(
        "codex/tier3-healthcheck-correction",
        ".github/workflows/tier3-release.yml",
        "ops/release/deploy_container.sh",
        "backend/app/main.py",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert ".github/workflows/tier3-release.yml" in rejected.stderr
    assert "ops/release/deploy_container.sh" in rejected.stderr
    assert "backend/app/main.py" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier2_components_accepts_replay_safe_slice_and_rejects_delivery_paths() -> None:
    accepted = _check(
        "codex/tier2-components",
        "backend/app/application/story_jobs.py",
        "backend/app/application/room_service.py",
        "backend/app/application/story_resolution.py",
        "backend/app/domain/story_jobs.py",
        "backend/app/domain/story_resolution.py",
        "backend/app/adapters/memory_story_job_queue.py",
        "backend/app/adapters/postgres_story_resolution_store.py",
        "backend/migrations/003_create_story_resolution_results.sql",
        "backend/tests/test_story_jobs.py",
        "backend/tests/test_story_resolution_workflow.py",
        "docs/decisions/0004-adopt-replay-safe-story-results.md",
        "docs/architecture/tier2-components.md",
    )
    rejected = _check(
        "codex/tier2-components",
        ".github/workflows/tier3-release.yml",
        "infra/cloudformation/tier3-delivery.yaml",
        "backend/app/api/routes.py",
        "backend/app/main.py",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert ".github/workflows/tier3-release.yml" in rejected.stderr
    assert "backend/app/api/routes.py" in rejected.stderr
    assert "backend/app/main.py" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_support_agent_core_accepts_isolated_paths_and_rejects_integration_paths() -> None:
    accepted = _check(
        "codex/support-agent-core",
        "backend/app/domain/support_agent.py",
        "backend/app/application/support_agent.py",
        "backend/app/application/support_ports.py",
        "backend/app/adapters/static_rules_knowledge_base.py",
        "backend/app/adapters/memory_support_report_repository.py",
        "backend/app/adapters/mock_support_model.py",
        "backend/app/resources/game_rules.json",
        "backend/tests/test_support_agent_contract.py",
        "docs/features/support-agent.md",
    )
    rejected = _check(
        "codex/support-agent-core",
        "backend/app/application/ports.py",
        "backend/app/application/room_service.py",
        "backend/app/api/routes.py",
        "backend/app/main.py",
        "backend/migrations/004_create_support_reports.sql",
        "web/src/ui/pages/support-page.js",
        "infra/cloudformation/tier5-agent.yaml",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/application/room_service.py" in rejected.stderr
    assert "backend/app/api/routes.py" in rejected.stderr
    assert "backend/migrations/004_create_support_reports.sql" in rejected.stderr
    assert "web/src/ui/pages/support-page.js" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier2_async_flow_accepts_integration_slice_and_rejects_delivery_paths() -> None:
    accepted = _check(
        "codex/tier2-async-flow",
        "backend/app/api/routes.py",
        "backend/app/main.py",
        "backend/app/adapters/story_resolution_narrator.py",
        "backend/app/workers/story_resolution_worker.py",
        "backend/tests/test_tier2_async_process_e2e.py",
        "web/src/ui/pages/game-page.js",
        "docs/features/tier2-async-flow.md",
    )
    rejected = _check(
        "codex/tier2-async-flow",
        ".github/workflows/tier3-release.yml",
        "Dockerfile",
        "infra/cloudformation/tier3-delivery.yaml",
        "backend/migrations/004_create_support_reports.sql",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert ".github/workflows/tier3-release.yml" in rejected.stderr
    assert "Dockerfile" in rejected.stderr
    assert "infra/cloudformation/tier3-delivery.yaml" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier2_production_worker_accepts_only_worker_and_storyteller_paths() -> None:
    accepted = _check(
        "codex/tier2-production-worker",
        "backend/app/adapters/bedrock_storyteller.py",
        "backend/app/adapters/production_storyteller_factory.py",
        "backend/app/adapters/story_resolution_narrator.py",
        "backend/app/main.py",
        "backend/app/workers/story_resolution_worker.py",
        "backend/tests/test_tier2_production_worker.py",
        "docs/features/tier2-async-flow.md",
    )
    rejected = _check(
        "codex/tier2-production-worker",
        "backend/app/api/routes.py",
        "backend/migrations/004_create_support_report_drafts.sql",
        "web/src/ui/pages/game-page.js",
        "Dockerfile",
        "infra/cloudformation/tier2-components.yaml",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/api/routes.py" in rejected.stderr
    assert "backend/migrations/004_create_support_report_drafts.sql" in rejected.stderr
    assert "Dockerfile" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_tier2_migration_bridge_accepts_only_compatibility_release_paths() -> None:
    accepted = _check(
        "codex/tier2-migration-bridge",
        ".github/workflows/tier3-release.yml",
        "backend/app/adapters/postgres_migrations.py",
        "backend/app/adapters/postgres_room_repository.py",
        "backend/app/adapters/production_storyteller_factory.py",
        "backend/app/main.py",
        "backend/tests/test_migration_readiness.py",
        "backend/tests/test_tier2_production_worker.py",
        "backend/tests/test_tier3_delivery_contract.py",
        "infra/cloudformation/tier3-delivery.yaml",
        "ops/release/deploy_container.sh",
        "ops/systemd/co-story-container.service",
        "docs/decisions/0006-adopt-tier2-migration-bridge.md",
    )
    rejected = _check(
        "codex/tier2-migration-bridge",
        "backend/app/adapters/bedrock_storyteller.py",
        "backend/migrations/004_create_support_report_drafts.sql",
        "web/src/ui/pages/game-page.js",
        "Dockerfile",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/adapters/bedrock_storyteller.py" in rejected.stderr
    assert "backend/migrations/004_create_support_report_drafts.sql" in rejected.stderr
    assert "Dockerfile" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_support_agent_persistence_accepts_only_local_draft_storage_paths() -> None:
    accepted = _check(
        "codex/support-agent-persistence",
        "backend/app/domain/support_agent.py",
        "backend/app/application/support_agent.py",
        "backend/app/adapters/memory_support_report_repository.py",
        "backend/app/adapters/postgres_support_report_repository.py",
        "backend/migrations/004_create_support_report_drafts.sql",
        "backend/tests/test_postgres_support_report_repository.py",
        "backend/tests/test_migration_readiness.py",
        "docs/features/support-agent-persistence.md",
    )
    rejected = _check(
        "codex/support-agent-persistence",
        "backend/app/application/support_ports.py",
        "backend/app/main.py",
        "backend/app/api/routes.py",
        "web/src/ui/pages/support-page.js",
        "backend/app/adapters/bedrock_storyteller.py",
        "infra/cloudformation/tier5-agent.yaml",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/main.py" in rejected.stderr
    assert "backend/app/api/routes.py" in rejected.stderr
    assert "backend/app/adapters/bedrock_storyteller.py" in rejected.stderr
    assert "docs/handoffs/CURRENT.md" in rejected.stderr


def test_support_agent_durability_accepts_only_parallel_storage_gate_paths() -> None:
    accepted = _check(
        "codex/support-agent-durability",
        "backend/app/adapters/postgres_support_report_repository.py",
        "backend/tests/test_postgres_support_report_repository.py",
        "backend/tests/test_postgres_support_report_process_e2e.py",
        "docs/features/support-agent-persistence.md",
        "docs/evidence/2026-08-28-support-agent-durability/validation.md",
    )
    rejected = _check(
        "codex/support-agent-durability",
        "backend/app/domain/support_agent.py",
        "backend/app/application/support_agent.py",
        "backend/migrations/004_create_support_report_drafts.sql",
        "backend/app/main.py",
        "backend/app/api/routes.py",
        "web/src/ui/pages/support-page.js",
        "infra/cloudformation/tier5-agent.yaml",
        "docs/handoffs/CURRENT.md",
    )

    assert accepted.returncode == 0, accepted.stderr
    assert rejected.returncode == 2
    assert "backend/app/domain/support_agent.py" in rejected.stderr
    assert "backend/migrations/004_create_support_report_drafts.sql" in rejected.stderr
    assert "backend/app/main.py" in rejected.stderr
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
    assert "codex/tier3-production-release" in guide
    assert "codex/tier3-healthcheck-correction" in guide
    assert "codex/tier2-components" in guide
    assert "codex/tier2-async-flow" in guide
    assert "codex/tier2-migration-bridge" in guide
    assert "codex/tier2-production-worker" in guide
    assert "codex/support-agent-core" in guide
    assert "codex/support-agent-durability" in guide
    assert "codex/support-agent-persistence" in guide
    assert "單一部署 owner" in guide
    assert "branch-boundary:" in workflow
    assert "scripts/check_branch_boundaries.py" in workflow
    assert "github.head_ref" in workflow
