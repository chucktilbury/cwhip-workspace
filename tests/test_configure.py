from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConfigureTests(unittest.TestCase):
    def test_workspace_staging_disables_sdk_registration(self):
        with tempfile.TemporaryDirectory(prefix="workspace sdk config ") as directory:
            work = Path(directory)
            source = work / "source"
            build = work / "build"
            source.mkdir()
            shutil.copyfile(ROOT / "CMakeLists.txt", source / "CMakeLists.txt")
            for name in ("cmake", "scripts"):
                shutil.copytree(ROOT / name, source / name)
            for component in ("compiler", "editor", "debugger", "cmacros", "website"):
                (source / component / ".git").mkdir(parents=True)
            for component in ("editor", "debugger", "cmacros"):
                (source / component / "CMakeLists.txt").touch()
            # Stand in for the component-owned installer, exercising the actual
            # workspace configure, recursive build, install and publication path.
            (source / "compiler/CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.24)
project(registration_probe NONE)
option(CWHIP_REGISTER_SDK "Register the installed SDK" ON)
if(CWHIP_REGISTER_SDK)
    message(FATAL_ERROR "Workspace must disable SDK registration")
endif()
file(WRITE "${CMAKE_BINARY_DIR}/cwhip" "#!/bin/sh\\nexit 0\\n")
file(WRITE "${CMAKE_BINARY_DIR}/cwhip-pkg" "#!/bin/sh\\nexit 0\\n")
add_custom_target(cwhip)
install(PROGRAMS "${CMAKE_BINARY_DIR}/cwhip"
    "${CMAKE_BINARY_DIR}/cwhip-pkg" DESTINATION bin)
""")
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("CWHIP_") and key not in
                   ("DESTDIR", "MAKEFLAGS", "MFLAGS", "MAKELEVEL")}
            configs = []
            for key in ("HOME", "XDG_CONFIG_HOME"):
                path = work / key.lower()
                path.mkdir()
                env[key] = str(path)
                configs.append(path / (".config/cwhip" if key == "HOME" else "cwhip"))

            def run(*command):
                result = subprocess.run(
                    [str(item) for item in command], env=env, cwd=work,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout)

            run("cmake", "-S", source, "-B", build, "-G", "Unix Makefiles",
                "-DCWHIP_GTK=OFF", "-DCWHIP_GTK_SOURCEVIEW=OFF",
                "-DCWHIP_BUILD_CMACROS=OFF", "-DBUILD_TESTING=OFF")
            run("cmake", "--build", build, "--target", "cwhip")
            for config in configs:
                self.assertFalse(config.exists(), config)
                config.mkdir(parents=True)
                (config / "sdk.toml").write_text('sdk_prefix = "/chosen/sdk"\n')
                (config / "settings.toml").write_text(
                    'sdk_prefix = "/legacy/sdk"\n[editor]\ntheme = "dark"\n')
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                      for config in configs for path in config.iterdir()}
            run("cmake", "--build", build, "--target", "cwhip")
            after = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                     for config in configs for path in config.iterdir()}
            self.assertEqual(before, after)
            self.assertTrue((source / "bin/cwhip").is_symlink())

    def test_missing_standalone_project_fails_before_compiler_configure(self):
        for missing in ("editor", "debugger", "cmacros"):
            with self.subTest(component=missing), tempfile.TemporaryDirectory(
                    prefix="workspace configure ") as directory:
                source = Path(directory) / "source"
                build = Path(directory) / "build"
                source.mkdir()
                shutil.copyfile(ROOT / "CMakeLists.txt", source / "CMakeLists.txt")
                for component in ("compiler", "editor", "debugger", "cmacros", "website"):
                    (source / component / ".git").mkdir(parents=True)
                for component in ("editor", "debugger", "cmacros"):
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
        for missing in ("editor", "debugger", "cmacros"):
            with self.subTest(component=missing), tempfile.TemporaryDirectory(
                    prefix="workspace test-all ") as directory:
                source = Path(directory) / "source"
                build = Path(directory) / "build"
                for component in ("editor", "debugger", "cmacros"):
                    (source / component).mkdir(parents=True)
                    if component != missing:
                        (source / component / "CMakeLists.txt").touch()
                command = [
                    sys.executable, str(ROOT / "scripts/test_all.py"),
                    "--source", str(source), "--build", str(build)]
                for option in ("cmake", "ctest", "cc", "cxx", "clang"):
                    command.extend(("--" + option, "must-not-run"))
                for option in ("gtk", "sourceview", "editor", "debugger", "cmacros"):
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
