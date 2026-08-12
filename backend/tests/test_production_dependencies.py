from pathlib import Path


PRODUCTION_REQUIREMENTS = Path(__file__).parents[1] / "requirements-prod.txt"
REQUIRED_PACKAGES = {"fastapi", "uvicorn[standard]", "psycopg[binary]", "boto3", "botocore"}
DEVELOPMENT_ONLY_PACKAGES = {"pytest", "httpx"}


def _requirements() -> list[str]:
    assert PRODUCTION_REQUIREMENTS.is_file(), "production dependency lock 尚未建立"
    return [
        line.strip()
        for line in PRODUCTION_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _package_name(requirement: str) -> str:
    return requirement.split("==", maxsplit=1)[0].lower()


def test_production_dependency_lock_pins_required_runtime_packages() -> None:
    requirements = _requirements()

    assert all("==" in requirement for requirement in requirements)
    assert REQUIRED_PACKAGES.issubset({_package_name(item) for item in requirements})


def test_production_dependency_lock_excludes_development_test_tools() -> None:
    requirements = _requirements()

    assert DEVELOPMENT_ONLY_PACKAGES.isdisjoint({_package_name(item) for item in requirements})
