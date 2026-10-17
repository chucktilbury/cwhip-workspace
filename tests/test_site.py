import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class SiteTests(unittest.TestCase):
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
