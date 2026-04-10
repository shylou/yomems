import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL = REPO_ROOT / "scripts" / "install.sh"
INSTALL_CODEX = REPO_ROOT / "scripts" / "install-codex.sh"
INSTALL_CLAUDE = REPO_ROOT / "scripts" / "install-claude.sh"


class InstallScriptTests(unittest.TestCase):
    def test_install_help(self) -> None:
        result = subprocess.run(
            ["bash", str(INSTALL), "help"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        self.assertIn("YOMEMS_TARGET_DIR", result.stdout)
        self.assertIn("install", result.stdout)
        self.assertIn("remove", result.stdout)

    def test_host_wrappers_set_expected_target_names(self) -> None:
        codex = subprocess.run(
            ["bash", str(INSTALL_CODEX), "help"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        claude = subprocess.run(
            ["bash", str(INSTALL_CLAUDE), "help"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        self.assertIn("Codex", codex.stdout)
        self.assertIn(".codex/skills", codex.stdout)
        self.assertIn("Claude Code", claude.stdout)
        self.assertIn(".claude/skills", claude.stdout)

    def test_install_and_remove_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-install-") as tmp_dir:
            target_root = Path(tmp_dir) / "skills"
            env = os.environ.copy()
            env["YOMEMS_TARGET_DIR"] = str(target_root)

            install_result = subprocess.run(
                ["bash", str(INSTALL), "install"],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            self.assertIn("Installed YOMems", install_result.stdout)

            installed_dir = target_root / "yomems"
            wrapper = installed_dir / "bin" / "yomems"
            self.assertTrue((installed_dir / "src" / "yomems" / "cli.py").exists())
            self.assertTrue((installed_dir / "design" / "architecture.md").exists())
            self.assertTrue((installed_dir / "schemas" / "memory-object.schema.json").exists())
            self.assertTrue((installed_dir / "templates" / "project_decision.md").exists())
            self.assertTrue((installed_dir / "SKILL.md").exists())
            self.assertTrue(wrapper.exists())
            self.assertTrue((installed_dir / "scripts" / "agent-wake.sh").exists())
            self.assertTrue((installed_dir / "scripts" / "agent-remember.sh").exists())
            self.assertTrue((installed_dir / "scripts" / "resolve-memory-root.sh").exists())

            wrapper_help = subprocess.run(
                ["bash", str(wrapper), "--help"],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            self.assertIn("yomems", wrapper_help.stdout)

            remove_result = subprocess.run(
                ["bash", str(INSTALL), "remove"],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            self.assertIn("Removed YOMems", remove_result.stdout)
            self.assertFalse(installed_dir.exists())
