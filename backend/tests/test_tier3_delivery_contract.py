import os
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).parents[2]
RELEASE_WORKFLOW = ROOT / ".github/workflows/tier3-release.yml"
TEMPLATE = ROOT / "infra/cloudformation/tier3-delivery.yaml"
RELEASE_SCRIPT = ROOT / "ops/release/deploy_container.sh"
REPOSITORY = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/co-story-tier3"
TARGET_DIGEST = "sha256:" + "2" * 64
PREVIOUS_DIGEST = "sha256:" + "1" * 64
TARGET_IMAGE_ID = "sha256:" + "a" * 64


def _read(path: Path) -> str:
    assert path.is_file(), f"Tier 3 asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def _write_executable(path: Path, content: str, mode: int = 0o755) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)


def _release_document_command() -> str:
    template = yaml.safe_load(_read(TEMPLATE))
    return template["Resources"]["ContainerReleaseDocument"]["Properties"]["Content"][
        "mainSteps"
    ][0]["inputs"]["runCommand"][0]


def _document_harness(
    tmp_path: Path,
    *,
    mode: str,
    stable_modes: str = "digest-release",
    asset_kind: str = "regular",
    asset_metadata: str = "",
    container_image_id: str = TARGET_IMAGE_ID,
    target_preflight_failure: bool = False,
    target_release_failure: bool = False,
    target_mutation: str = "",
) -> tuple[subprocess.CompletedProcess[str], list[str], Path, Path, Path]:
    """Run the rendered SSM command against a bounded fake host and registry."""

    host = tmp_path / "host"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    events = tmp_path / "events.log"
    runtime_env = host / "etc/co-story/runtime.env"
    rds_ca = host / "etc/pki/rds/rds-ca.pem"
    stable_driver = host / "usr/local/libexec/co-story-deploy-container"
    stable_unit = host / "usr/local/share/co-story/co-story-container.service"
    marker = host / "etc/co-story/migration-bridge.state"
    active_state = host / "etc/co-story/container-transition.state"
    for directory in (
        runtime_env.parent,
        rds_ca.parent,
        stable_driver.parent,
        stable_unit.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    runtime_env.write_text("CO_STORY_ALLOWED_HOSTS=localhost\n", encoding="utf-8")
    rds_ca.write_text("test-ca\n", encoding="utf-8")
    stable_unit.write_text("[Service]\n", encoding="utf-8")

    _write_executable(
        stable_driver,
        "#!/bin/sh\n"
        "printf 'stable:%s:%s\\n' \"$1\" \"${9:-release}\" >>\"$TEST_EVENTS\"\n"
        "case \",$TEST_STABLE_MODES,\" in *\",$1,\"*) exit 0 ;; *) exit 42 ;; esac\n",
        0o500,
    )
    target_driver = tmp_path / "target-deploy-container.sh"
    _write_executable(
        target_driver,
        "#!/bin/sh\n"
        "printf 'target:%s:%s:%s:%s\\n' \"$1\" \"${9:-release}\" \"$7\" \"$8\" >>\"$TEST_EVENTS\"\n"
        "test \"$1\" = migration-bridge || exit 43\n"
        "if test \"${9:-release}\" = preflight-only; then\n"
        "  test \"$TEST_TARGET_PREFLIGHT_FAILURE\" = 1 && exit 44\n"
        "  case \"$TEST_TARGET_MUTATION\" in\n"
        "    driver) chmod 0700 \"$8\"; printf '# replaced\\n' >>\"$8\" ;;\n"
        "    unit) chmod 0600 \"$7\"; printf '# replaced\\n' >>\"$7\" ;;\n"
        "  esac\n"
        "  exit 0\n"
        "fi\n"
        "test \"$TEST_TARGET_RELEASE_FAILURE\" = 1 && exit 45\n"
        "mkdir -p \"$(dirname \"$TEST_ACTIVE_STATE\")\"\n"
        "printf 'STATE=container-active\\n' >\"$TEST_ACTIVE_STATE\"\n"
        "printf 'STATE=verified-bridge\\n' >\"$TEST_MARKER\"\n",
        0o500,
    )
    target_unit = tmp_path / "target-container.service"
    target_unit.write_text("[Service]\n", encoding="utf-8")
    target_unit.chmod(0o400)

    _write_executable(fake_bin / "aws", "#!/bin/sh\nprintf 'registry-login\\n'\n")
    _write_executable(
        fake_bin / "readlink",
        "#!/bin/sh\n"
        "if test \"$1\" = -f; then shift; fi\n"
        "printf '%s\\n' \"$1\"\n",
    )
    _write_executable(
        fake_bin / "stat",
        "#!/bin/sh\n"
        "for path; do :; done\n"
        "case \"$path\" in\n"
        "  *rds-ca.pem) printf 'root:root:644\\n' ;;\n"
        "  *deploy_container.sh) printf '%s\\n' \"${TEST_ASSET_METADATA:-root:root:500}\" ;;\n"
        "  *co-story-container.service) printf '%s\\n' \"${TEST_ASSET_METADATA:-root:root:400}\" ;;\n"
        "  *) printf 'root:root:700\\n' ;;\n"
        "esac\n",
    )
    _write_executable(
        fake_bin / "docker",
        "#!/bin/sh\n"
        "printf 'docker:%s\\n' \"$*\" >>\"$TEST_EVENTS\"\n"
        "case \"$1\" in\n"
        "  login) cat >/dev/null ;;\n"
        "  pull|create|rm) ;;\n"
        "  image) test \"$2\" = inspect && printf '%s\\n' \"$TEST_TARGET_IMAGE_ID\" ;;\n"
        "  inspect) printf '%s\\n' \"$TEST_CONTAINER_IMAGE_ID\" ;;\n"
        "  cp)\n"
        "    destination=\"$3\"\n"
        "    case \"$2\" in\n"
        "      *deploy_container.sh) source=\"$TEST_TARGET_DRIVER\" ;;\n"
        "      *co-story-container.service) source=\"$TEST_TARGET_UNIT\" ;;\n"
        "      *) exit 61 ;;\n"
        "    esac\n"
        "    case \"$TEST_ASSET_KIND\" in\n"
        "      missing) : ;;\n"
        "      symlink) ln -s \"$source\" \"$destination\" ;;\n"
        "      directory) mkdir \"$destination\" ;;\n"
        "      *) cp -p \"$source\" \"$destination\" ;;\n"
        "    esac\n"
        "    ;;\n"
        "  *) exit 62 ;;\n"
        "esac\n",
    )

    replacements = {
        "{{ RepositoryUri }}": REPOSITORY,
        "{{ ImageDigest }}": TARGET_DIGEST,
        "{{ PreviousImageDigest }}": PREVIOUS_DIGEST,
        "{{ ReleaseMode }}": mode,
        "{{ ExpectedLegacyRelease }}": "",
        "/etc/co-story/runtime.env": str(runtime_env),
        "/etc/pki/rds/rds-ca.pem": str(rds_ca),
        "/usr/local/libexec/co-story-deploy-container": str(stable_driver),
        "/usr/local/share/co-story/co-story-container.service": str(stable_unit),
    }
    command = _release_document_command()
    for source, destination in replacements.items():
        command = command.replace(source, destination)
    document = tmp_path / "release-document.sh"
    _write_executable(document, command)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "TEST_EVENTS": str(events),
            "TEST_STABLE_MODES": stable_modes,
            "TEST_TARGET_DRIVER": str(target_driver),
            "TEST_TARGET_UNIT": str(target_unit),
            "TEST_TARGET_IMAGE_ID": TARGET_IMAGE_ID,
            "TEST_CONTAINER_IMAGE_ID": container_image_id,
            "TEST_ASSET_KIND": asset_kind,
            "TEST_ASSET_METADATA": asset_metadata,
            "TEST_TARGET_PREFLIGHT_FAILURE": "1" if target_preflight_failure else "0",
            "TEST_TARGET_RELEASE_FAILURE": "1" if target_release_failure else "0",
            "TEST_TARGET_MUTATION": target_mutation,
            "TEST_MARKER": str(marker),
            "TEST_ACTIVE_STATE": str(active_state),
        }
    )
    result = subprocess.run(
        ["bash", str(document)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, events.read_text(encoding="utf-8").splitlines() if events.exists() else [], marker, active_state, tmp_path


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


def test_release_workflow_validates_bridge_and_schema_activation_before_credentials_or_build() -> None:
    workflow_text = _read(RELEASE_WORKFLOW)
    workflow = yaml.safe_load(workflow_text)
    steps = workflow["jobs"]["deploy"]["steps"]
    input_validation = next(
        index for index, step in enumerate(steps)
        if step.get("name") == "Validate mutually exclusive release inputs"
    )
    credentials = next(
        index for index, step in enumerate(steps)
        if step.get("name") == "Configure bounded AWS credentials"
    )
    build = next(
        index for index, step in enumerate(steps)
        if step.get("name") == "Build and push immutable commit image"
    )

    assert input_validation < credentials < build
    validation = steps[input_validation]["run"]
    assert "migration-bridge)" in validation
    assert "schema-activation)" in validation
    assert "bridge requires a previous digest" in validation
    assert "schema activation requires a previous digest" in validation


def test_release_workflow_scans_exact_pushed_digest_as_linux_arm64() -> None:
    workflow = yaml.safe_load(_read(RELEASE_WORKFLOW))
    deploy_steps = workflow["jobs"]["deploy"]["steps"]
    scan_steps = [
        step
        for step in deploy_steps
        if step.get("name") == "Scan the exact pushed digest"
    ]

    assert len(scan_steps) == 1
    scan_step = scan_steps[0]
    assert scan_step["uses"] == "aquasecurity/trivy-action@v0.36.0"
    assert scan_step.get("env", {}).get("TRIVY_PLATFORM") == "linux/arm64"
    assert scan_step["with"] == {
        "version": "v0.70.0",
        "image-ref": (
            "${{ steps.ecr.outputs.registry }}/"
            "${{ vars.TIER3_ECR_REPOSITORY }}@${{ steps.build.outputs.digest }}"
        ),
        "severity": "CRITICAL,HIGH",
        "ignore-unfixed": True,
        "exit-code": 1,
    }


def test_release_workflow_validates_one_canonical_instance_target_before_build(
    tmp_path: Path,
) -> None:
    workflow_text = _read(RELEASE_WORKFLOW)
    workflow = yaml.safe_load(workflow_text)
    deploy_steps = workflow["jobs"]["deploy"]["steps"]
    validation_index = next(
        index
        for index, step in enumerate(deploy_steps)
        if step.get("name") == "Validate canonical deployment target"
    )
    credentials_index = next(
        index
        for index, step in enumerate(deploy_steps)
        if step.get("name") == "Configure bounded AWS credentials"
    )
    build_index = next(
        index
        for index, step in enumerate(deploy_steps)
        if step.get("name") == "Build and push immutable commit image"
    )
    validation = deploy_steps[validation_index]

    assert validation_index < credentials_index < build_index
    assert validation["env"] == {
        "UNVALIDATED_TIER3_INSTANCE_ID": "${{ vars.TIER3_INSTANCE_ID }}"
    }
    assert workflow_text.count("${{ vars.TIER3_INSTANCE_ID }}") == 1
    assert "xargs" not in validation["run"]
    assert " sed " not in validation["run"]
    assert " tr " not in validation["run"]

    github_env = tmp_path / "github.env"
    env = os.environ.copy()
    env.update(
        {
            "UNVALIDATED_TIER3_INSTANCE_ID": "i-0123456789abcdef0",
            "GITHUB_ENV": str(github_env),
        }
    )
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", validation["run"]],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert github_env.read_text(encoding="utf-8") == (
        "VALIDATED_TIER3_INSTANCE_ID=i-0123456789abcdef0\n"
    )

    release_step = next(
        step
        for step in deploy_steps
        if step.get("name") == "Release exact digest through bounded SSM document"
    )
    release_command = release_step["run"]
    assert '--targets "Key=InstanceIds,Values=$VALIDATED_TIER3_INSTANCE_ID"' in (
        release_command
    )
    assert release_command.count('$VALIDATED_TIER3_INSTANCE_ID"') == 3


@pytest.mark.parametrize(
    "invalid_instance_id",
    (
        " i-0123456789abcdef0",
        "i-0123456789abcdef0 ",
        "\ti-0123456789abcdef0",
        "i-0123456789abcdef0\n",
        "i-0123456789abcdef0\r\n",
        "i-01234567",
        "i-0123456789ABCDEf0",
    ),
)
def test_release_workflow_rejects_noncanonical_instance_target_without_trimming(
    tmp_path: Path, invalid_instance_id: str
) -> None:
    workflow = yaml.safe_load(_read(RELEASE_WORKFLOW))
    validation = next(
        step
        for step in workflow["jobs"]["deploy"]["steps"]
        if step.get("name") == "Validate canonical deployment target"
    )
    github_env = tmp_path / "github.env"
    env = os.environ.copy()
    env.update(
        {
            "UNVALIDATED_TIER3_INSTANCE_ID": invalid_instance_id,
            "GITHUB_ENV": str(github_env),
        }
    )

    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", validation["run"]],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert not github_env.exists() or github_env.read_text(encoding="utf-8") == ""


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
        'test ! -e "$stable_driver"',
        'test ! -e "$stable_unit"',
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
    digest_preflight = digest_block.index("preflight-only")
    digest_pull = digest_block.index('docker pull "$target_image"')
    assert digest_preflight < digest_pull
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


def test_release_document_validates_host_ca_before_first_registry_login_and_pull() -> None:
    template_text = _read(TEMPLATE)
    release_document = template_text[
        template_text.index("ContainerReleaseDocument:") : template_text.index(
            "LegacyRollbackDocument:"
        )
    ]
    first_login = release_document.index("aws ecr get-login-password")
    first_pull = release_document.index('docker pull "$target_image"')

    for guard in (
        "validate_rds_ca()",
        'test -f "$rds_ca"',
        'test ! -L "$rds_ca"',
        'readlink -f "$rds_ca"',
        "root:root:",
        "unsafe_rds_ca_permissions",
        "rds_ca_not_app_readable",
    ):
        assert release_document.index(guard) < first_login < first_pull
    assert release_document.count("validate_rds_ca") >= 3


def _event_index(events: list[str], prefix: str) -> int:
    return next(index for index, event in enumerate(events) if event.startswith(prefix))


def test_migration_bridge_bootstraps_an_old_stable_driver_with_the_target_driver(
    tmp_path: Path,
) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path, mode="migration-bridge"
    )

    assert result.returncode == 0, result.stderr
    ordered = (
        "stable:digest-release:preflight-only",
        "docker:login",
        f"docker:pull {REPOSITORY}@{TARGET_DIGEST}",
        "docker:create",
        "docker:cp",
        "target:migration-bridge:preflight-only",
        "target:migration-bridge:release",
    )
    positions = [_event_index(events, prefix) for prefix in ordered]
    assert positions == sorted(positions)
    preflight = events[_event_index(events, "target:migration-bridge:preflight-only")]
    release = events[_event_index(events, "target:migration-bridge:release")]
    assert preflight.split(":", 3)[3] == release.split(":", 3)[3]
    assert "app.commands.migrate" not in "\n".join(events)
    assert marker.is_file()
    assert active_state.is_file()


def test_schema_activation_keeps_using_the_upgraded_stable_driver(tmp_path: Path) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path,
        mode="schema-activation",
        stable_modes="schema-activation",
    )

    assert result.returncode == 0, result.stderr
    assert events.count("stable:schema-activation:preflight-only") == 1
    assert events.count("stable:schema-activation:release") == 1
    assert not any(event.startswith("target:") for event in events)
    assert not marker.exists()
    assert not active_state.exists()


@pytest.mark.parametrize(
    ("asset_kind", "asset_metadata"),
    (
        ("missing", ""),
        ("symlink", ""),
        ("directory", ""),
        ("regular", "root:root:700"),
        ("regular", "root:co-story:500"),
    ),
)
def test_migration_bridge_rejects_unsafe_temporary_assets_before_target_execution(
    tmp_path: Path, asset_kind: str, asset_metadata: str
) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path,
        mode="migration-bridge",
        stable_modes="digest-release,migration-bridge",
        asset_kind=asset_kind,
        asset_metadata=asset_metadata,
    )

    assert result.returncode != 0
    assert not any(event.startswith("target:") for event in events)
    assert not marker.exists()
    assert not active_state.exists()


def test_migration_bridge_rejects_an_asset_container_not_bound_to_target_image(
    tmp_path: Path,
) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path,
        mode="migration-bridge",
        stable_modes="digest-release,migration-bridge",
        container_image_id="sha256:" + "b" * 64,
    )

    assert result.returncode != 0
    assert not any(event.startswith("target:") for event in events)
    assert not marker.exists()
    assert not active_state.exists()


@pytest.mark.parametrize("target_mutation", ("driver", "unit"))
def test_migration_bridge_rejects_asset_substitution_after_target_preflight(
    tmp_path: Path, target_mutation: str
) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path,
        mode="migration-bridge",
        stable_modes="digest-release,migration-bridge",
        target_mutation=target_mutation,
    )

    assert result.returncode != 0
    assert any(event.startswith("target:migration-bridge:preflight-only") for event in events)
    assert not any(event.startswith("target:migration-bridge:release") for event in events)
    assert not marker.exists()
    assert not active_state.exists()


@pytest.mark.parametrize("failure", ("preflight", "release"))
def test_migration_bridge_failure_does_not_declare_a_verified_bridge(
    tmp_path: Path, failure: str
) -> None:
    result, events, marker, active_state, _ = _document_harness(
        tmp_path,
        mode="migration-bridge",
        stable_modes="digest-release,migration-bridge",
        target_preflight_failure=failure == "preflight",
        target_release_failure=failure == "release",
    )

    assert result.returncode != 0
    if failure == "preflight":
        assert not any(event.startswith("target:migration-bridge:release") for event in events)
    assert not marker.exists()
    assert not active_state.exists()
