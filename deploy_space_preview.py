"""Publish the reviewed preview files to the existing Angel Chat Space.

HF_TOKEN is read only by the command entry point. It is never saved, included in
the upload, or used to read secret values. This command cannot send email.
"""

import json
import os
from pathlib import Path
import re
import shutil
import tempfile


SPACE_ID = "lvRJay18950/Prayer-Angel"
PREVIEW_FLAGS = ("EMAIL_SIGNUPS_ENABLED", "EMAIL_DELIVERY_ENABLED")
RUNTIME_FILES = (
    "app.py", "daily_encouragement.py", "email_subscription.py", "email_ui.py",
    "supabase_email_store.py", "hostinger_email.py", "email_worker.py",
    "email_connection_check.py", "requirements.txt", "Dockerfile", "README.md",
    "EMAIL_SETUP.md", "EMAIL_PRIVACY_NOTICE.md",
)


class PreviewDeploymentError(Exception):
    """Only fixed, local explanations may be shown in deployment logs."""


def require_disabled_email(api):
    # Secrets are write-only: this endpoint returns names/metadata, not values.
    secret_names = api.get_space_secrets(repo_id=SPACE_ID)
    variables = api.get_space_variables(repo_id=SPACE_ID)
    if any(flag in secret_names for flag in PREVIEW_FLAGS):
        raise PreviewDeploymentError("Email enable flags must be variables, not secrets, for a verifiable preview.")
    for flag in PREVIEW_FLAGS:
        variable = variables.get(flag)
        if variable is not None and variable.value.strip().lower() not in ("", "false"):
            raise PreviewDeploymentError("Preview blocked: email signup and delivery must both be disabled.")
    # Missing variables use the application's tested false defaults.


def deploy_preview(api, root, source_sha):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise PreviewDeploymentError("A full GitHub source commit is required.")
    root = Path(root)
    for name in RUNTIME_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise PreviewDeploymentError("A required preview file is missing or is a symbolic link.")
    require_disabled_email(api)
    previous_sha = api.repo_info(repo_id=SPACE_ID, repo_type="space").sha
    with tempfile.TemporaryDirectory(prefix="angel-preview-") as directory:
        staged = Path(directory)
        for name in RUNTIME_FILES:
            shutil.copyfile(root / name, staged / name)
        (staged / "deployment.json").write_text(json.dumps({
            "source_repository": "jLvRjay-coder/Prayer-Angel-App",
            "source_commit": source_sha,
            "mode": "daily-encouragement-preview",
        }, indent=2) + "\n", encoding="utf-8")
        # One atomic source commit, with a parent guard. No remote deletions:
        # existing stories, icons, and other assets remain in the Space.
        commit = api.upload_folder(
            repo_id=SPACE_ID, repo_type="space", folder_path=directory,
            revision="main", parent_commit=previous_sha,
            commit_message=f"Preview Daily Encouragement from {source_sha[:12]}",
        )
    require_disabled_email(api)
    return commit.oid


def main():
    token = os.environ.get("HF_TOKEN", "")
    if not token or token != token.strip():
        print("FAIL: HF_TOKEN is missing or has surrounding whitespace.")
        return 1
    try:
        from huggingface_hub import HfApi

        commit = deploy_preview(
            HfApi(token=token), Path(__file__).resolve().parent,
            os.environ.get("GITHUB_SHA", ""),
        )
    except PreviewDeploymentError as error:
        print(f"FAIL: {error}")
        return 1
    except Exception:
        # Provider exception text can contain headers or other private details.
        print(f"FAIL: Space deployment failed. Verify HF_TOKEN has write access to {SPACE_ID}.")
        return 1
    if not re.fullmatch(r"[0-9a-f]{40}", str(commit)):
        print("FAIL: Hugging Face did not return a recognizable commit.")
        return 1
    print(f"PASS: Preview uploaded to {SPACE_ID}")
    print(f"Space commit: {commit}")
    print("PASS: Email signup and delivery are disabled. No email sent.")
    print("The Space will rebuild. Check its runtime and public page before declaring deployment complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
