import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class SiteTests(unittest.TestCase):
    def _make_workspace(self, workspace):
        for name in (
            "website/build.py",
            "website/check_site.py",
            "compiler/doc/GETTING_STARTED.md",
            "editor/CEDIT.md",
            "debugger/CDBG.md",
            "cmacros/README.md",
            "cmacros/doc/BUILD.md",
            "cmacros/doc/LANGUAGE.md",
            "cmacros/doc/DIAGNOSTICS.md",
            "cmacros/examples/README.md",
            "doc/FIRST-PROGRAM.md",
        ):
            path = workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture")
        (workspace / "website/build.py").write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "output = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
            "output.mkdir(parents=True, exist_ok=True)\n"
            "(output / 'index.html').write_text('site')\n"
        )

    def _run_site_adapter(self, workspace, work):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_site.py"),
                "--workspace", str(workspace),
                "--work", str(work),
            ],
            capture_output=True,
            text=True,
        )

    def test_real_pinned_inputs(self):
        with tempfile.TemporaryDirectory(prefix="workspace site ") as directory:
            work = Path(directory)
            site.build(ROOT, work, None)
            output = work / "doc/website/site"
            for document in (ROOT / "compiler/doc").glob("*.md"):
                if document.name in ("CEDIT.md", "CDBG.md", "GETTING_STARTED.md"):
                    continue
                page = output / (document.stem + ".html")
                self.assertTrue(page.is_file(), page)
                text = page.read_text()
                self.assertTrue("<main>" in text or "canonical" in text, page)
            for page in ("getting-started/index.html", "cmacros/README.html",
                         "cmacros/doc/BUILD.html", "cmacros/doc/LANGUAGE.html",
                         "cmacros/doc/DIAGNOSTICS.html", "cmacros/examples/README.html",
                         "editor/CEDIT.html", "debugger/CDBG.html"):
                self.assertTrue((output / page).is_file(), page)
            for asset in ("styles.css", "app.js"):
                self.assertEqual((output / asset).read_bytes(),
                                 (ROOT / "website/content" / asset).read_bytes())
            self.assertIn("LANGUAGE-REFERENCE.html", (output / "docs.html").read_text())
            self.assertIn("Macro Processor (cmacros)", (output / "docs.html").read_text())
            self.assertNotIn("./html/index.html", (output / "docs.html").read_text())
            self.assertIn("Cwhip", (output / "index.html").read_text())
            stale = output / "stale.html"
            stale.touch()
            api = work / "api"
            api.mkdir()
            (api / "index.html").write_text("Existing API reference")
            site.build(ROOT, work, api)
            self.assertFalse(stale.exists())
            self.assertEqual((output / "html/index.html").read_text(), "Existing API reference")

    def test_source_tree_work_paths_fail_before_deleting_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            self._make_workspace(workspace)
            for component in ("compiler", "cmacros"):
                marker = workspace / component / "doc/keep.txt"
                marker.write_text("source must survive")
                result = self._run_site_adapter(workspace, workspace / component)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("overlaps protected workspace input", result.stderr)
                self.assertEqual(marker.read_text(), "source must survive")

    def test_symlinked_source_work_path_fails_before_deleting_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            self._make_workspace(workspace)
            marker = workspace / "compiler/doc/keep.txt"
            marker.write_text("source must survive")
            work_link = workspace / "compiler-link"
            work_link.symlink_to(workspace / "compiler", target_is_directory=True)
            result = self._run_site_adapter(workspace, work_link)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("overlaps protected workspace input", result.stderr)
            self.assertEqual(marker.read_text(), "source must survive")

    def test_symlinked_doc_stage_fails_before_deleting_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            self._make_workspace(workspace)
            marker = workspace / "cmacros/doc/keep.txt"
            marker.write_text("source must survive")
            work = workspace / "build/website"
            (work / "doc").parent.mkdir(parents=True)
            (work / "doc").symlink_to(
                workspace / "cmacros/doc",
                target_is_directory=True,
            )
            result = self._run_site_adapter(workspace, work)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("overlaps protected workspace input", result.stderr)
            self.assertEqual(marker.read_text(), "source must survive")

    def test_binary_tree_work_path_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            self._make_workspace(workspace)
            work = workspace / "build/website"
            result = self._run_site_adapter(workspace, work)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                (work / "doc/website/site/index.html").read_text(),
                "site",
            )

    def test_invalid_api_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "lacks index.html"):
                site.build(ROOT, Path(directory) / "work", Path(directory) / "missing")

    def test_missing_document_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Required workspace website input missing"):
                site.build(Path(directory) / "empty-workspace", Path(directory) / "staging", None)


if __name__ == "__main__":
    unittest.main()
