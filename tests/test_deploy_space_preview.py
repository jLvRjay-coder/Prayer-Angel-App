import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import deploy_space_preview as deployment
from email_subscription import EmailSettings


class PreviewDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in deployment.RUNTIME_FILES:
            (self.root / name).write_text("reviewed source", encoding="utf-8")
        (self.root / ".env").write_text("secret-must-not-upload")
        (self.root / "private.json").write_text("subscriber-must-not-upload")
        self.api = Mock()
        self.api.get_space_secrets.return_value = {"OPENAI_API_KEY": object()}
        self.api.get_space_variables.return_value = {}
        self.api.repo_info.return_value.sha = "a" * 40
        self.api.upload_folder.return_value.oid = "b" * 40

    def test_only_explicit_files_upload_with_parent_guard_and_no_deletions(self):
        def upload(**arguments):
            self.assertEqual(arguments["repo_id"], deployment.SPACE_ID)
            self.assertEqual(arguments["repo_type"], "space")
            self.assertEqual(arguments["parent_commit"], "a" * 40)
            self.assertEqual(arguments["revision"], "main")
            self.assertNotIn("delete_patterns", arguments)
            staged = Path(arguments["folder_path"])
            self.assertEqual({p.name for p in staged.iterdir()}, set(deployment.RUNTIME_FILES) | {"deployment.json"})
            self.assertEqual(json.loads((staged / "deployment.json").read_text())["source_commit"], "c" * 40)
            return SimpleNamespace(oid="b" * 40)
        self.api.upload_folder.side_effect = upload
        self.assertEqual(deployment.deploy_preview(self.api, self.root, "c" * 40), "b" * 40)
        self.api.upload_folder.assert_called_once()
        self.assertEqual(self.api.get_space_variables.call_count, 2)
        self.assertFalse(EmailSettings.from_env({}).signups_enabled)
        self.assertFalse(EmailSettings.from_env({}).delivery_enabled)

    def test_enabled_or_unverifiable_flags_block_before_any_upload(self):
        for flag in deployment.PREVIEW_FLAGS:
            for value in ("true", "TRUE", "yes", "1"):
                with self.subTest(flag=flag, value=value):
                    self.api.get_space_variables.return_value = {flag: SimpleNamespace(value=value)}
                    with self.assertRaises(deployment.PreviewDeploymentError):
                        deployment.deploy_preview(self.api, self.root, "c" * 40)
                    self.api.upload_folder.assert_not_called()
            self.api.get_space_variables.return_value = {}
            self.api.get_space_secrets.return_value = {flag: object()}
            with self.assertRaises(deployment.PreviewDeploymentError):
                deployment.deploy_preview(self.api, self.root, "c" * 40)
            self.api.upload_folder.assert_not_called()
            self.api.get_space_secrets.return_value = {}

    def test_missing_or_symlinked_source_and_invalid_commit_block_upload(self):
        with self.assertRaises(deployment.PreviewDeploymentError):
            deployment.deploy_preview(self.api, self.root, "not-a-commit")
        path = self.root / deployment.RUNTIME_FILES[0]
        path.unlink()
        with self.assertRaises(deployment.PreviewDeploymentError):
            deployment.deploy_preview(self.api, self.root, "c" * 40)
        path.symlink_to(self.root / ".env")
        with self.assertRaises(deployment.PreviewDeploymentError):
            deployment.deploy_preview(self.api, self.root, "c" * 40)
        self.api.upload_folder.assert_not_called()

    def test_provider_errors_and_token_values_are_not_logged(self):
        token = "hf_fake_private_token_for_test"
        fake_module = SimpleNamespace(HfApi=Mock(side_effect=RuntimeError(token)))
        output = io.StringIO()
        with patch.dict("os.environ", {"HF_TOKEN": token}), patch.dict("sys.modules", {"huggingface_hub": fake_module}), contextlib.redirect_stdout(output):
            self.assertEqual(deployment.main(), 1)
        self.assertNotIn(token, output.getvalue())
        self.assertIn("write access", output.getvalue())


if __name__ == "__main__":
    unittest.main()
