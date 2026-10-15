import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publish_bin", ROOT / "scripts/publish_bin.py")
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_switch_repair_noop_and_disabled_apps(self):
        with tempfile.TemporaryDirectory(prefix="bin publication ") as directory:
            root = Path(directory)
            output = root / "bin"
            for build in ("first", "second"):
                stage = root / build
                (stage / "bin").mkdir(parents=True)
                for name in publication.NAMES:
                    binary = stage / "bin" / name
                    binary.write_text("#!/bin/sh\nexit 0\n")
                    binary.chmod(0o755)
            first, second = root / "first", root / "second"
            publication.publish(first, output, list(publication.NAMES), list(publication.NAMES))
            before = {p.name: p.lstat().st_mtime_ns for p in output.iterdir()}
            publication.publish(first, output, list(publication.NAMES), list(publication.NAMES))
            self.assertEqual(before, {p.name: p.lstat().st_mtime_ns for p in output.iterdir()})
            (output / "cwhip").unlink()
            publication.publish(first, output, ["cwhip", "cwhip-pkg"], list(publication.NAMES))
            self.assertEqual((output / "cwhip").resolve(), first / "bin/cwhip")
            publication.publish(second, output, ["cwhip", "cwhip-pkg"], ["cwhip", "cwhip-pkg"])
            self.assertEqual((output / "cwhip").resolve(), second / "bin/cwhip")
            self.assertFalse((output / "cedit").is_symlink())
            self.assertFalse((output / "cedit.bin").is_symlink())
            self.assertFalse((output / "cdbg").is_symlink())
            (output / "cwhip").unlink()
            (output / "cwhip").write_text("User file")
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                publication.publish(first, output, ["cwhip"], ["cwhip"])


if __name__ == "__main__":
    unittest.main()
