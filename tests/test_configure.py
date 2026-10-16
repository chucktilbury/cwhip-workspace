from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConfigureTests(unittest.TestCase):
    def test_missing_standalone_project_fails_before_compiler_configure(self):
        for missing in ("editor", "debugger"):
            with self.subTest(component=missing), tempfile.TemporaryDirectory(
                    prefix="workspace configure ") as directory:
                source = Path(directory) / "source"
                build = Path(directory) / "build"
                source.mkdir()
                shutil.copyfile(ROOT / "CMakeLists.txt", source / "CMakeLists.txt")
                for component in ("compiler", "editor", "debugger", "website"):
                    (source / component / ".git").mkdir(parents=True)
                for component in ("editor", "debugger"):
                    if component != missing:
                        (source / component / "CMakeLists.txt").touch()
                result = subprocess.run(
                    ["cmake", "-S", str(source), "-B", str(build),
                     "-G", "Unix Makefiles", "-DCWHIP_GTK=OFF",
                     "-DCWHIP_GTK_SOURCEVIEW=OFF"],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=60)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                output = " ".join(result.stdout.split())
                self.assertIn(f"Missing standalone {missing} project", output)
                self.assertIn(str(source / missing / "CMakeLists.txt"), output)
                self.assertIn("workspace submodule pins updated", output)
                self.assertIn(f'cmake -S "{source / missing}"', output)
                self.assertFalse((build / "compiler-build").exists())

    def test_test_all_preflights_before_creating_build_outputs(self):
        for missing in ("editor", "debugger"):
            with self.subTest(component=missing), tempfile.TemporaryDirectory(
                    prefix="workspace test-all ") as directory:
                source = Path(directory) / "source"
                build = Path(directory) / "build"
                for component in ("editor", "debugger"):
                    (source / component).mkdir(parents=True)
                    if component != missing:
                        (source / component / "CMakeLists.txt").touch()
                command = [
                    sys.executable, str(ROOT / "scripts/test_all.py"),
                    "--source", str(source), "--build", str(build)]
                for option in ("cmake", "ctest", "cc", "cxx", "clang"):
                    command.extend(("--" + option, "must-not-run"))
                for option in ("gtk", "sourceview", "editor", "debugger"):
                    command.extend(("--" + option, "OFF"))
                result = subprocess.run(
                    command, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=30)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"Missing standalone {missing} project", result.stdout)
                self.assertIn(str(source / missing / "CMakeLists.txt"), result.stdout)
                self.assertIn("workspace submodule pins updated", result.stdout)
                self.assertFalse(build.exists())


if __name__ == "__main__":
    unittest.main()
