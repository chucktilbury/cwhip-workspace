import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clean_build", ROOT / "scripts/clean_build.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanTests(unittest.TestCase):
    def test_scoped_idempotent_cleanup_and_link_ownership(self):
        with tempfile.TemporaryDirectory(prefix="workspace clean ") as directory:
            root = Path(directory)
            build = root / "build"
            other = root / "other"
            public = root / "bin"
            public.mkdir()
            for base in (build, other):
                for name in ("stage/bin", "compiler-stage", "tests", "website", "Testing", "test-all",
                             "apps/cedit/home", "apps/cdbg/src", "compiler-build",
                             "CMakeFiles/cedit_launcher.dir", "CMakeFiles/cdbg_terminal.dir"):
                    (base / name).mkdir(parents=True)
                    (base / name / "artifact").touch()
                for app in ("cedit", "cdbg"):
                    (base / "apps" / app / "inputs.txt").write_text("configure state")
                (base / "CMakeCache.txt").write_text("root configuration")
            (public / "cwhip").symlink_to(build / "stage/bin/cwhip")
            (public / "cdbg").symlink_to(other / "stage/bin/cdbg")
            (public / "cedit").write_text("unowned regular file")
            cleanup.clean(build, public)
            cleanup.clean(build, public)
            self.assertFalse((public / "cwhip").is_symlink())
            self.assertEqual((public / "cdbg").readlink(), other / "stage/bin/cdbg")
            self.assertEqual((public / "cedit").read_text(), "unowned regular file")
            for name in ("stage", "compiler-stage", "tests", "website", "Testing", "test-all"):
                self.assertFalse((build / name).exists(), name)
                self.assertTrue((other / name / ("bin/artifact" if name == "stage" else "artifact")).exists())
            for app in ("cedit", "cdbg"):
                self.assertFalse((build / "apps" / app).exists())
                self.assertTrue((other / "apps" / app / "inputs.txt").is_file())
            for name in ("cedit_launcher", "cdbg_terminal"):
                self.assertFalse((build / "CMakeFiles" / (name + ".dir")).exists())
                self.assertTrue((other / "CMakeFiles" / (name + ".dir") / "artifact").is_file())
            self.assertTrue((build / "CMakeCache.txt").exists())
            self.assertTrue((build / "compiler-build/artifact").exists())


if __name__ == "__main__":
    unittest.main()
