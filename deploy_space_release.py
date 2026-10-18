"""Deploy the main-branch release and apply the owner's email switches.

GitHub repository variables are the release controls. Secret values are never
read back or logged. Uploads use the same explicit file list and parent guard as
the preview deployment. This command does not send email.
"""

import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from deploy_space_preview import RUNTIME_FILES, SPACE_ID, PREVIEW_FLAGS


def release_flags(values):
    result = {}
    for flag in PREVIEW_FLAGS:
        value = values.get(flag, "false").strip().lower()
        if value not in {"true", "false"}:
            raise ValueError("Email release switches must be true or false.")
        result[flag] = value
    return result


def deploy_release(api, root, source_sha, flags):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("A full source commit is required.")
    flags = release_flags(flags)
    secret_names = api.get_space_secrets(repo_id=SPACE_ID)
    if any(flag in secret_names for flag in PREVIEW_FLAGS):
        raise ValueError("Email enable flags must be variables, not secrets.")
    root = Path(root)
    for name in RUNTIME_FILES:
        if not (root / name).is_file() or (root / name).is_symlink():
            raise ValueError("A required release file is missing or is a symbolic link.")
    previous_sha = api.repo_info(repo_id=SPACE_ID, repo_type="space").sha
    # Pause signups during the source update. Never change any subscriber record.
    api.add_space_variable(repo_id=SPACE_ID, key="EMAIL_SIGNUPS_ENABLED", value="false")
    api.add_space_variable(repo_id=SPACE_ID, key="EMAIL_DELIVERY_ENABLED", value="false")
    with tempfile.TemporaryDirectory(prefix="angel-release-") as directory:
        staged = Path(directory)
        for name in RUNTIME_FILES:
            shutil.copyfile(root / name, staged / name)
        (staged / "deployment.json").write_text(json.dumps({
            "source_repository": "jLvRjay-coder/Prayer-Angel-App",
            "source_commit": source_sha,
            "mode": "daily-encouragement-release",
        }, indent=2) + "\n", encoding="utf-8")
        commit = api.upload_folder(
            repo_id=SPACE_ID, repo_type="space", folder_path=directory,
            revision="main", parent_commit=previous_sha,
            commit_message=f"Release Daily Encouragement from {source_sha[:12]}",
        )
    if not re.fullmatch(r"[0-9a-f]{40}", str(commit.oid)):
        raise ValueError("Space did not return a recognizable commit.")
    for flag, value in flags.items():
        api.add_space_variable(repo_id=SPACE_ID, key=flag, value=value)
    variables = api.get_space_variables(repo_id=SPACE_ID)
    if any(variables.get(flag) is None or variables[flag].value != value for flag, value in flags.items()):
        raise ValueError("Space email switches did not match the release controls.")
    return commit.oid


def main():
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        print("FAIL: Release deployment requires the main branch.")
        return 1
    token = os.environ.get("HF_TOKEN", "")
    if not token or token != token.strip():
        print("FAIL: HF_TOKEN is missing or has surrounding whitespace.")
        return 1
    try:
        from huggingface_hub import HfApi
        commit = deploy_release(HfApi(token=token), Path(__file__).resolve().parent,
                                os.environ.get("GITHUB_SHA", ""), release_flags(os.environ))
    except Exception:
        print("FAIL: Release deployment stopped. Check source files, Space access, and email switch configuration. No email sent.")
        return 1
    print(f"PASS: Release source uploaded. Space commit: {commit}")
    print("PASS: Space email switches match the repository release controls. No email sent by deployment.")
    print("Verify the rebuilt public app before announcing the launch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
