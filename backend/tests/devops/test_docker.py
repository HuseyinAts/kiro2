"""
Docker configuration tests (DO-01).

Tests that Docker files exist and have required configurations.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend to path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def test_dockerfile_exists():
    """Test that backend Dockerfile exists."""
    dockerfile_path = Path(backend_dir) / "Dockerfile"

    assert dockerfile_path.exists(), (
        f"Dockerfile should exist at: {dockerfile_path}"
    )
    assert dockerfile_path.is_file(), (
        f"Dockerfile should be a file, not directory: {dockerfile_path}"
    )


def test_production_dockerfile_exists():
    """Test that production Dockerfile exists."""
    dockerfile_path = Path(backend_dir) / "Dockerfile.production"

    assert dockerfile_path.exists(), (
        f"Dockerfile.production should exist at: {dockerfile_path}"
    )
    assert dockerfile_path.is_file(), (
        f"Dockerfile.production should be a file: {dockerfile_path}"
    )


def test_dockerignore_exists():
    """Test that .dockerignore file exists."""
    # .dockerignore should be in backend or project root
    backend_dockerignore = Path(backend_dir) / ".dockerignore"
    root_dockerignore = Path(backend_dir).parent / ".dockerignore"

    exists = backend_dockerignore.exists() or root_dockerignore.exists()

    assert exists, (
        ".dockerignore should exist in backend or project root"
    )


def test_docker_compose_exists():
    """Test that docker-compose.yml exists."""
    # docker-compose.yml typically in project root
    compose_path = Path(backend_dir).parent / "docker-compose.yml"

    assert compose_path.exists(), (
        f"docker-compose.yml should exist at: {compose_path}"
    )
    assert compose_path.is_file(), (
        f"docker-compose.yml should be a file: {compose_path}"
    )


def test_dockerfile_has_nonroot_user():
    """Test that Dockerfile configures non-root user."""
    dockerfile_path = Path(backend_dir) / "Dockerfile"

    if not dockerfile_path.exists():
        pytest.skip("Dockerfile not found")

    content = dockerfile_path.read_text(encoding="utf-8")

    # Check for USER instruction
    has_user_instruction = "USER" in content

    assert has_user_instruction, (
        "Dockerfile should configure non-root user with USER instruction"
    )

    # USER should not be root
    lines = content.split("\n")
    user_lines = [line.strip() for line in lines if line.strip().startswith("USER")]

    if user_lines:
        # Verify at least one USER line is not root
        has_nonroot = any(
            not line.endswith("root") and not line.endswith("0")
            for line in user_lines
        )
        assert has_nonroot, "Dockerfile should set USER to non-root user"


def test_dockerfile_has_healthcheck():
    """Test that Dockerfile includes HEALTHCHECK instruction."""
    dockerfile_path = Path(backend_dir) / "Dockerfile"

    if not dockerfile_path.exists():
        pytest.skip("Dockerfile not found")

    content = dockerfile_path.read_text(encoding="utf-8")

    # Check for HEALTHCHECK instruction
    has_healthcheck = "HEALTHCHECK" in content

    assert has_healthcheck, (
        "Dockerfile should include HEALTHCHECK instruction for container health monitoring"
    )

    # If healthcheck exists, verify it has CMD
    if has_healthcheck:
        lines = content.split("\n")
        healthcheck_lines = [
            line.strip() for line in lines
            if "HEALTHCHECK" in line
        ]

        # CMD may be on a continuation line after HEALTHCHECK
        has_cmd = "CMD" in content[content.index("HEALTHCHECK"):]
        assert has_cmd, "HEALTHCHECK should specify CMD"
