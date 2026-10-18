import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from deploy_space_preview import RUNTIME_FILES
from deploy_space_release import deploy_release, main, release_flags


class ReleaseDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in RUNTIME_FILES:
            (self.root / name).write_text("source")
        (self.root / "private.json").write_text("never-upload")
        self.api = Mock()
        self.api.get_space_secrets.return_value = {}
        self.api.repo_info.return_value.sha = "a" * 40
        self.api.upload_folder.return_value.oid = "b" * 40
        self.flags = {"EMAIL_SIGNUPS_ENABLED": "true", "EMAIL_DELIVERY_ENABLED": "true"}
        self.api.get_space_variables.return_value = {k: SimpleNamespace(value=v) for k, v in self.flags.items()}

    def test_only_reviewed_files_upload_before_activation_with_parent_guard(self):
        def upload(**kwargs):
            self.assertEqual(kwargs["parent_commit"], "a" * 40)
            self.assertNotIn("delete_patterns", kwargs)
            staged = Path(kwargs["folder_path"])
            self.assertEqual({p.name for p in staged.iterdir()}, set(RUNTIME_FILES) | {"deployment.json"})
            self.assertEqual(json.loads((staged / "deployment.json").read_text())["mode"], "daily-encouragement-release")
            self.assertEqual([c.kwargs["value"] for c in self.api.add_space_variable.call_args_list], ["false", "false"])
            return SimpleNamespace(oid="b" * 40)
        self.api.upload_folder.side_effect = upload
        self.assertEqual(deploy_release(self.api, self.root, "c" * 40, self.flags), "b" * 40)
        self.assertEqual([c.kwargs["value"] for c in self.api.add_space_variable.call_args_list], ["false", "false", "true", "true"])

    def test_failed_upload_leaves_controls_paused(self):
        self.api.upload_folder.side_effect = RuntimeError("provider-private-detail")
        with self.assertRaises(RuntimeError):
            deploy_release(self.api, self.root, "c" * 40, self.flags)
        self.assertEqual([c.kwargs["value"] for c in self.api.add_space_variable.call_args_list], ["false", "false"])

    def test_invalid_switch_secret_flag_and_missing_file_block_mutations(self):
        with self.assertRaises(ValueError):
            release_flags({"EMAIL_DELIVERY_ENABLED": "yes"})
        self.api.get_space_secrets.return_value = {"EMAIL_DELIVERY_ENABLED": object()}
        with self.assertRaises(ValueError):
            deploy_release(self.api, self.root, "c" * 40, self.flags)
        self.api.get_space_secrets.return_value = {}
        (self.root / RUNTIME_FILES[0]).unlink()
        with self.assertRaises(ValueError):
            deploy_release(self.api, self.root, "c" * 40, self.flags)
        self.api.upload_folder.assert_not_called()
        self.api.add_space_variable.assert_not_called()

    def test_release_entrypoint_refuses_other_branches(self):
        with patch.dict("os.environ", {"GITHUB_REF": "refs/heads/preview"}):
            self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
