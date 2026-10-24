"""Prove installed SDK relocation and independent application project interfaces."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
HELLO = """import math as M
class Bridge {
    int64 answer()
    void message() {
        inline() { fputs("inline;", stdout); }
    }
}
int64 Bridge.answer() from "external_answer"
start {
    Bridge b()
    b.message()
    print(M.Math().sqrt(9.0) == 3.0)
    print(b.answer())
}
"""
PROJECT = """cmake_minimum_required(VERSION 3.24)
project(external_sdk_user LANGUAGES C)
find_package(Cwhip 0.0.2 EXACT CONFIG REQUIRED)
if(NOT Cwhip_SDK_ABI STREQUAL "numeric-v2")
    message(FATAL_ERROR "external project requires the Cwhip numeric-v2 SDK ABI")
endif()
add_library(binding OBJECT native.c)
target_include_directories(binding PRIVATE "${Cwhip_INCLUDE_DIR}")
cwhip_add_program(hello SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/hello.cw"
    OBJECTS $<TARGET_OBJECTS:binding> DEPENDS binding)
get_target_property(binary hello CWHIP_EXECUTABLE)
install(PROGRAMS "${binary}" DESTINATION bin)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--ctest", default="ctest")
    parser.add_argument("--apps", choices=("ON", "OFF"), default="ON")
    parser.add_argument("--cmacros", choices=("ON", "OFF"), default="ON")
    args = parser.parse_args()
    # test-all intentionally sets TMPDIR inside its build; this check must leave it.
    with tempfile.TemporaryDirectory(prefix="cwhip standalone acceptance ", dir="/tmp") as directory:
        work = Path(directory)
        original = work / "sdk original"
        relocated = work / "sdk relocated"
        shutil.copytree(args.prefix.resolve(), original)
        original.rename(relocated)
        assert not original.exists()
        clean_env = {key: value for key, value in os.environ.items()
               if not key.startswith("CWHIP_") and key not in (
                   "CC", "DESTDIR", "DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
                   "MAKEFLAGS", "MFLAGS", "MAKELEVEL", "CTEST_PARALLEL_LEVEL", "CMAKE_PREFIX_PATH",
                   "Cwhip_DIR", "Cwhip_ROOT")}
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
                    "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = work / key.lower()
            path.mkdir(mode=0o700)
            clean_env[key] = str(path)
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PATH"] = str(relocated / "bin") + os.pathsep + os.pathsep.join(
            part for part in os.get_exec_path() if not Path(part).is_relative_to(ROOT))

        def run(*command, fail=False, env=None):
            print("+", " ".join(map(str, command)), flush=True)
            result = subprocess.run([str(item) for item in command],
                                    env=env if env is not None else clean_env, cwd=work,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=900)
            print(result.stdout, end="", flush=True)
            if fail:
                assert result.returncode != 0, "Invalid SDK configuration unexpectedly succeeded"
            else:
                result.check_returncode()
            return result

        # Config scripts are the exported interface, not original build-tree metadata.
        for config in relocated.rglob("*.cmake"):
            text = config.read_text()
            assert str(ROOT) not in text and str(args.prefix.resolve()) not in text, config
        paths = run(relocated / "bin/cwhip", "--print-paths").stdout
        assert str(relocated) in paths and str(ROOT) not in paths, paths
        assert "executable-relative" in paths, paths
        # Exercise the beginner's actual tracked example through both interfaces.
        beginner = work / "first program"
        shutil.copytree(ROOT / "examples/hello-world", beginner)
        run(relocated / "bin/cwhip", beginner / "hello.cw", "-o", beginner / "hello")
        assert run(beginner / "hello").stdout == "Hello, world!\n"
        beginner_build = beginner / "build"
        run(args.cmake, "-S", beginner, "-B", beginner_build, "-G", "Unix Makefiles",
            f"-DCMAKE_PREFIX_PATH={relocated}")
        run(args.cmake, "--build", beginner_build, "--parallel", "4")
        assert run(beginner_build / "bin/hello").stdout == "Hello, world!\n"
        source = beginner / "hello.cw"
        source.write_text(source.read_text().replace("Hello, world!", "Hello from Cwhip!"))
        run(relocated / "bin/cwhip", source, "-o", beginner / "hello")
        assert run(beginner / "hello").stdout == "Hello from Cwhip!\n"
        run(args.cmake, "--build", beginner_build, "--parallel", "4")
        assert run(beginner_build / "bin/hello").stdout == "Hello from Cwhip!\n"
        project = work / "external project"
        project.mkdir()
        (project / "CMakeLists.txt").write_text(PROJECT)
        (project / "hello.cw").write_text(HELLO)
        (project / "native.c").write_text(
            '#include <cwhip/Stdlib.h>\n#include <stdint.h>\n'
            'int64_t external_answer(void *self) { (void)self; return 42; }\n')
        binary = project / "build output"
        run(args.cmake, "-S", project, "-B", binary, f"-DCMAKE_PREFIX_PATH={relocated}")
        run(args.cmake, "--build", binary, "--parallel", "4")
        result = run(binary / "bin/hello")
        assert result.stdout == "inline;true42", result.stdout
        stamp = (binary / "bin/hello").stat().st_mtime_ns
        run(args.cmake, "--build", binary, "--parallel", "4")
        assert (binary / "bin/hello").stat().st_mtime_ns == stamp
        run(args.cmake, "--build", binary, "--target", "clean")
        assert not (binary / "bin/hello").exists()
        run(args.cmake, "--build", binary, "--parallel", "4")
        run(args.cmake, "--install", binary, "--prefix", work / "hello installed")
        assert run(work / "hello installed/bin/hello").stdout == "inline;true42"
        runtime = next(relocated.glob("lib*/cwhip/libcwhip_runtime.a"))
        hidden = runtime.with_suffix(".unavailable")
        runtime.rename(hidden)
        try:
            run(args.cmake, "-S", project, "-B", work / "incomplete sdk",
                f"-DCMAKE_PREFIX_PATH={relocated}", fail=True)
        finally:
            hidden.rename(runtime)
        wrong_version = work / "wrong version"
        wrong_version.mkdir()
        (wrong_version / "CMakeLists.txt").write_text(PROJECT.replace("0.0.2", "999.0.0"))
        run(args.cmake, "-S", wrong_version, "-B", work / "incompatible sdk",
            f"-DCMAKE_PREFIX_PATH={relocated}", fail=True)
        if args.cmacros == "ON":
            app_source = work / "cmacros source"
            shutil.copytree(ROOT / "cmacros", app_source, ignore=shutil.ignore_patterns(
                ".git", "build*", "__pycache__"))
            app_build = work / "cmacros build"
            cmacros_env = clean_env.copy()
            cmacros_env["CWHIP_SDK"] = str(relocated)
            run(args.cmake, "-S", app_source, "-B", app_build,
                f"-DCMAKE_PREFIX_PATH={relocated}", "-DCMAKE_BUILD_TYPE=Debug",
                f"-DCWHIP_BIN_DIR={app_build / 'bin'}",
                f"-DCWHIP_LIB_DIR={app_build / 'lib'}",
                env=cmacros_env)
            run(args.cmake, "--build", app_build, "--parallel", "4")
            run(args.ctest, "--test-dir", app_build, "--output-on-failure", "--parallel", "1")
            installed = work / "cmacros installed"
            run(args.cmake, "--install", app_build, "--prefix", installed)
            moved = work / "cmacros relocated"
            installed.rename(moved)
            assert run(moved / "bin/cmacros", "--version").stdout == "cmacros: v1.0\n"
            run(args.cmake, "--build", app_build, "--target", "clean")
            assert not (app_build / "bin/cmacros").exists()
            run(args.cmake, "--build", app_build, "--parallel", "4")
            run(args.ctest, "--test-dir", app_build, "--output-on-failure", "--parallel", "1")
        else:
            print("EXCLUDED: independent cmacros SDK/build/install/relocation suite (--cmacros OFF)")
        if args.apps == "ON":
            for app in ("editor", "debugger"):
                app_source = work / (app + " source")
                shutil.copytree(ROOT / app, app_source, ignore=shutil.ignore_patterns(
                    ".git", "build*", "__pycache__"))
                app_build = work / (app + " build")
                run(args.cmake, "-S", app_source, "-B", app_build,
                    f"-DCMAKE_PREFIX_PATH={relocated}", "-DCMAKE_BUILD_TYPE=Debug")
                run(args.cmake, "--build", app_build, "--target", "test-all", "--parallel", "4")
                run(args.cmake, "--build", app_build, "--target", "check-noop")
                installed = work / (app + " installed")
                run(args.cmake, "--install", app_build, "--prefix", installed)
                moved = work / (app + " relocated")
                installed.rename(moved)
                if app == "debugger":
                    result = run(moved / "bin/cdbg", "--help")
                    assert "Usage: cdbg" in result.stdout
                elif shutil.which("Xvfb") and shutil.which("dbus-daemon"):
                    run("python3", app_source / "tests/test_smoke.py",
                        "--executable", moved / "bin/cedit", "--xvfb", shutil.which("Xvfb"),
                        "--work", work / "installed editor checks")
                else:
                    print("EXCLUDED: installed editor headless launch needs Xvfb and dbus-daemon")
                run(args.cmake, "--build", app_build, "--target", "clean")
                assert not list((app_build / "bin").glob("*"))
                run(args.cmake, "--build", app_build, "--parallel", "4")
                run(args.ctest, "--test-dir", app_build, "--output-on-failure", "--parallel", "1")
                for config in (moved / "share").rglob("*"):
                    if config.is_file():
                        assert str(ROOT) not in config.read_text(), config
        else:
            print("EXCLUDED: independent application relocation suites (--apps OFF)")
        print("SDK relocation and external project acceptance passed", flush=True)


if __name__ == "__main__":
    main()
