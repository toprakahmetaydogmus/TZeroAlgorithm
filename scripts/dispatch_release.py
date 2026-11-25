"""Create a release and dispatch existing publishers after trusted main CI passes."""

import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)


def require_success(result, operation):
    if result.returncode:
        raise RuntimeError(f"{operation} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def dispatch_release(root, repository, commit):
    """Publish only the current, CI-tested main commit; leave existing releases alone."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid repository")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full commit SHA")
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Automatic releases require a stable X.Y.Z version")
    tag = f"v{version}"
    current = require_success(
        gh("api", f"repos/{repository}/git/ref/heads/main", "--jq", ".object.sha"),
        "Read main commit",
    )
    if current != commit:
        return {"skipped": "main advanced after this CI run", "tag": tag}

    existing = gh("api", f"repos/{repository}/releases/tags/{tag}")
    if existing.returncode == 0:
        return {"skipped": "release already exists", "tag": tag}
    if "HTTP 404" not in existing.stderr:
        require_success(existing, "Check existing release")

    notes = root / "docs" / "releases" / f"{tag}.md"
    note_args = ["--notes-file", str(notes)] if notes.is_file() else ["--generate-notes"]
    require_success(
        gh("release", "create", tag, "--repo", repository, "--target", commit,
           "--title", f"T-Zero {tag}", "--latest", *note_args),
        "Create GitHub Release",
    )
    publishers = {
        "release.yml": ["tag_name=" + tag],
        "publish-npm.yml": [],
        "publish-pypi.yml": [],
        "publish-extension.yml": ["publish_openvsx=true", "publish_vscode=true"],
        "publish-huggingface.yml": [],
        "rust-core.yml": ["upload_release=true"],
    }
    dispatched, failed = [], []
    for workflow, inputs in publishers.items():
        args = ["workflow", "run", workflow, "--repo", repository, "--ref", tag]
        for value in inputs:
            args.extend(["--field", value])
        result = gh(*args)
        if result.returncode:
            failed.append(f"{workflow}: {result.stderr.strip()}")
        else:
            dispatched.append(workflow)
    if failed:
        raise RuntimeError("Some publication workflows could not be started: " + "; ".join(failed))
    return {"tag": tag, "dispatched": dispatched, "publication": "pending registry verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(dispatch_release(root, args.repository, args.commit)))


if __name__ == "__main__":
    main()
