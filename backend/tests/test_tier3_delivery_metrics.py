import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
WRITER = ROOT / "ops/release/write_delivery_metrics.py"
WORKFLOW = ROOT / ".github/workflows/tier3-release.yml"


def _run_writer(tmp_path: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    output = tmp_path / "delivery-metrics.json"
    result = subprocess.run(
        [
            "python3",
            WRITER,
            "--output",
            output,
            "--status",
            "success",
            "--commit-sha",
            "a" * 40,
            "--workflow-run-id",
            "12345",
            "--request-epoch",
            "100",
            "--approval-epoch",
            "130",
            "--deploy-start-epoch",
            "140",
            "--artifact-ready-epoch",
            "200",
            "--release-start-epoch",
            "210",
            "--completed-epoch",
            "240",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result, output


def test_metrics_writer_emits_sanitized_comparable_automatic_timing(tmp_path: Path) -> None:
    result, output = _run_writer(tmp_path)

    assert result.returncode == 0, result.stderr
    metrics = json.loads(output.read_text(encoding="utf-8"))
    assert metrics == {
        "schema_version": 1,
        "method": "automatic",
        "status": "success",
        "verified": True,
        "commit_sha": "a" * 40,
        "workflow_run_id": "12345",
        "human_interaction_count": 2,
        "timestamps_epoch": {
            "request": 100,
            "approval": 130,
            "deploy_start": 140,
            "artifact_ready": 200,
            "release_start": 210,
            "completed": 240,
        },
        "durations_seconds": {
            "approval_wait": 30,
            "automation_execution": 100,
            "build_and_scan": 60,
            "ssm_release_attempt": 30,
            "end_to_end": 140,
        },
    }
    serialized = output.read_text(encoding="utf-8").lower()
    assert "account" not in serialized
    assert "instance" not in serialized
    assert "role" not in serialized
    assert "token" not in serialized


def test_metrics_writer_rejects_reversed_or_untrusted_measurements(tmp_path: Path) -> None:
    reversed_result, _ = _run_writer(
        tmp_path,
        "--completed-epoch",
        "90",
    )
    assert reversed_result.returncode == 2
    assert "timestamps" in reversed_result.stderr.lower()

    unsafe_output = tmp_path / "unsafe.json"
    unsafe_result = subprocess.run(
        [
            "python3",
            WRITER,
            "--output",
            unsafe_output,
            "--status",
            "success",
            "--commit-sha",
            "refs/heads/main",
            "--workflow-run-id",
            "12345",
            "--request-epoch",
            "100",
            "--completed-epoch",
            "200",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert unsafe_result.returncode == 2
    assert not unsafe_output.exists()


def test_release_workflow_preserves_timing_artifact_even_when_deploy_fails() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "record-request:" in workflow
    assert "requested_epoch" in workflow
    assert "approved_epoch" in workflow
    assert "artifact_ready_epoch" in workflow
    assert "release_started_epoch" in workflow
    assert "write_delivery_metrics.py" in workflow
    assert "if: always()" in workflow
    assert "actions/upload-artifact@" in workflow
    assert "name: tier3-delivery-metrics-${{ github.run_id }}" in workflow
    assert "retention-days: 30" in workflow
    assert "outputs/tier3-delivery-metrics.json" in workflow
