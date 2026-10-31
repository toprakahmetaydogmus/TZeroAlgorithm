# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero CI/CD Pipeline & Security Gate Generator.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Installs zero-dependency, automated CI/CD security and verification pipelines:
  - GitHub Actions: .github/workflows/tzero_guard.yml
  - GitLab CI: .gitlab-ci.yml
  - Pre-commit: .pre-commit-config.yaml
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
from typing import Tuple, Dict, Any


GITHUB_WORKFLOW_TEMPLATE = """name: T-Zero Autonomous Quality & Zero-Leak Gate

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  tzero-verify:
    name: T-Zero Autonomous Verification Gate
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout Codebase
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 fastmcp keyring requests

      - name: Zero-Leak Security & Code Quality Audit
        run: |
          python tzero_v3.py --audit . --format text

      - name: Enforce T-4 Architectural Boundary Rules
        run: |
          python tzero_v3.py --enforce-boundaries tzero.rules.json

      - name: Run Comprehensive Test Suite
        run: |
          python -m unittest discover -s tests -p "test_*.py" -v

      - name: PR Incremental Token Savings Telemetry
        if: github.event_name == 'pull_request'
        run: |
          python tzero_v3.py --diff HEAD~1
"""

GITLAB_CI_TEMPLATE = """stages:
  - audit
  - test

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

tzero_audit:
  stage: audit
  image: python:3.11-slim
  script:
    - pip install --upgrade pip
    - pip install fastmcp keyring requests
    - python tzero_v3.py --audit . --format text
    - python tzero_v3.py --enforce-boundaries tzero.rules.json

tzero_tests:
  stage: test
  image: python:3.11-slim
  script:
    - pip install --upgrade pip
    - pip install fastmcp keyring requests
    - python -m unittest discover -s tests -p "test_*.py" -v
"""

PRE_COMMIT_CONFIG_TEMPLATE = """repos:
  - repo: local
    hooks:
      - id: tzero-zero-leak
        name: T-Zero 100% Zero-Leak Security Scanner
        entry: python tzero_v3.py --audit .
        language: system
        pass_filenames: false
        always_run: true

      - id: tzero-architectural-boundaries
        name: T-Zero Architectural Boundaries Enforcer
        entry: python tzero_v3.py --enforce-boundaries
        language: system
        pass_filenames: false
        always_run: true
"""


class CIPipelineGenerator:
    """Turnkey generator for automated enterprise CI/CD verification workflows."""

    @classmethod
    def install_github_workflow(cls, repo_dir: str = ".") -> Tuple[bool, str]:
        """Installs GitHub Actions workflow into .github/workflows/tzero_guard.yml."""
        wf_dir = os.path.join(repo_dir, ".github", "workflows")
        os.makedirs(wf_dir, exist_ok=True)
        wf_path = os.path.join(wf_dir, "tzero_guard.yml")
        with open(wf_path, "w", encoding="utf-8") as f:
            f.write(GITHUB_WORKFLOW_TEMPLATE.strip() + "\n")
        return True, wf_path

    @classmethod
    def install_gitlab_ci(cls, repo_dir: str = ".") -> Tuple[bool, str]:
        """Installs GitLab CI configuration into .gitlab-ci.yml."""
        ci_path = os.path.join(repo_dir, ".gitlab-ci.yml")
        with open(ci_path, "w", encoding="utf-8") as f:
            f.write(GITLAB_CI_TEMPLATE.strip() + "\n")
        return True, ci_path

    @classmethod
    def install_pre_commit(cls, repo_dir: str = ".") -> Tuple[bool, str]:
        """Installs pre-commit configuration into .pre-commit-config.yaml."""
        pc_path = os.path.join(repo_dir, ".pre-commit-config.yaml")
        with open(pc_path, "w", encoding="utf-8") as f:
            f.write(PRE_COMMIT_CONFIG_TEMPLATE.strip() + "\n")
        return True, pc_path
