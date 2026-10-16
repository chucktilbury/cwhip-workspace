from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "status.py"
COMPONENTS = ("compiler", "editor", "debugger", "website")


class StatusTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()

    def init_repo(self, root):
        root.mkdir()
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Workspace Test")
        self.git(root, "config", "user.email", "workspace-test@example.invalid")
        self.git(root, "config", "commit.gpgsign", "false")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cwhip-status-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        source = base / "source"
        self.init_repo(source)
        (source / "source.txt").write_text("initial\n")
        self.git(source, "add", ".")
        self.git(source, "commit", "-qm", "Initial component")
        self.pin = self.git(source, "rev-parse", "HEAD")
        self.root = base / "workspace with spaces"
        self.init_repo(self.root)
        (self.root / "scripts").mkdir()
        shutil.copy2(SCRIPT, self.root / "scripts" / "status.py")
        for name in COMPONENTS:
            self.git(self.root, "-c", "protocol.file.allow=always",
                     "submodule", "add", "-q", str(source), name)
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-qm", "Initial workspace")

    def run_status(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "status.py"), *args],
            cwd=self.temp.name, text=True, capture_output=True,
        )

    def test_clean_pins_from_other_directory(self):
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            f"{name}: pinned={self.pin} current={self.pin} OK"
            for name in COMPONENTS
        ])
        self.assertEqual(self.git(self.root, "status", "--porcelain"), "")

    def test_uninitialized_component(self):
        self.git(self.root, "submodule", "deinit", "-f", "--", "editor")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"editor: pinned={self.pin} current=- UNINITIALIZED", result.stdout)
        self.assertIn("website:", result.stdout)
        self.assertIn("git submodule update --init --checkout editor", result.stdout)
        self.assertNotIn("git add", result.stdout)
        self.assertEqual(self.run_status("--allow-dirty").returncode, 1)

    def test_tracked_dirty_component(self):
        (self.root / "editor" / "source.txt").write_text("changed\n")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"editor: pinned={self.pin} current={self.pin} DIRTY", result.stdout)
        allowed = self.run_status("--allow-dirty")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertIn("DIRTY", allowed.stdout)
        self.assertNotIn("git add", allowed.stdout)

    def test_untracked_dirty_component(self):
        (self.root / "debugger" / "new.txt").write_text("untracked\n")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"debugger: pinned={self.pin} current={self.pin} DIRTY", result.stdout)

    def test_staged_gitlink_still_compares_with_head(self):
        component = self.root / "compiler"
        self.git(component, "-c", "user.name=Workspace Test",
                 "-c", "user.email=workspace-test@example.invalid",
                 "-c", "commit.gpgsign=false",
                 "commit", "--allow-empty", "-qm", "New component revision")
        current = self.git(component, "rev-parse", "HEAD")
        self.git(self.root, "add", "compiler")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"compiler: pinned={self.pin} current={current} MISMATCH", result.stdout)
        self.assertIn("Pins are read from workspace HEAD, not the index", result.stdout)
        self.assertIn("component commits are pushed to their remotes", result.stdout)
        self.assertIn("git add compiler\n", result.stdout)
        self.assertIn('git commit -m "Update component pins"', result.stdout)
        self.assertIn("git push", result.stdout)
        self.assertIn("git submodule update --init --checkout compiler", result.stdout)
        self.assertEqual(self.run_status("--allow-dirty").returncode, 1)

    def test_hint_lists_only_mismatched_components(self):
        for name in ("editor", "debugger"):
            self.git(self.root / name, "-c", "user.name=Workspace Test",
                     "-c", "user.email=workspace-test@example.invalid",
                     "-c", "commit.gpgsign=false",
                     "commit", "--allow-empty", "-qm", "New revision")
        result = self.run_status("--allow-dirty")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Pin MISMATCH: editor debugger.", result.stdout)
        self.assertIn("git add editor debugger\n", result.stdout)
        self.assertIn("git submodule update --init --checkout editor debugger", result.stdout)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--name-only"), "")

    def test_git_error_is_reported(self):
        (self.root / "editor" / ".git").write_text("gitdir: missing\n")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn("status:", result.stderr)
        self.assertIn("fatal:", result.stderr)

    def test_missing_pin_is_reported(self):
        self.git(self.root, "rm", "-qf", "website")
        self.git(self.root, "commit", "-qm", "Remove component")
        result = self.run_status()
        self.assertEqual(result.returncode, 1)
        self.assertIn("website: HEAD does not contain a component Git link", result.stderr)


if __name__ == "__main__":
    unittest.main()
