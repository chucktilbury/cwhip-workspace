"""Run compiler, external application and workspace suites in isolated trees."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "build"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("cmake", "ctest", "cc", "cxx", "clang", "gtk", "sourceview", "editor", "debugger"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    source, build = args.source.resolve(), args.build.resolve()
    for component in ("editor", "debugger"):
        project = source / component / "CMakeLists.txt"
        if not project.is_file():
            raise RuntimeError(
                f"Missing standalone {component} project: {project}\n"
                "This workspace requires the standalone component CMake interfaces. "
                "The checked-out component revision is too old or incomplete. "
                "Uncommitted additions in another component worktree are not included "
                "by workspace commits or submodule pins.\n"
                "Use the isolated checkout containing those component changes, or wait "
                "for the standalone component revisions to be committed/tagged and the "
                "workspace submodule pins updated, then initialize those selected revisions "
                "explicitly. Do not copy uncommitted component files implicitly.\n"
                f'The application configure would use: cmake -S "{source / component}" '
                "-B <application-build-directory>")
    work = build / "test-all"
    work.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("CWHIP_") and key not in
           ("DESTDIR", "CC", "DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
            "MAKEFLAGS", "MFLAGS", "MAKELEVEL", "CTEST_PARALLEL_LEVEL")}
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "xdg"),
                      ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"),
                      ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        path = work / name
        path.mkdir(mode=0o700, exist_ok=True)
        env[key] = str(path)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    temporary = work / "tmp"
    temporary.mkdir(exist_ok=True)
    env["TMPDIR"] = str(temporary)

    def run(*command):
        print("+", " ".join(map(str, command)), flush=True)
        subprocess.run([str(item) for item in command], cwd=work, env=env, check=True)

    gtk = args.gtk == "ON"
    sourceview = args.sourceview == "ON"
    headless = gtk and all(shutil.which(tool) for tool in ("Xvfb", "dbus-daemon"))
    if not headless:
        print("EXCLUDED: compiler and external GUI sessions require enabled GTK "
              "bindings, Xvfb and dbus-daemon.", flush=True)
    suite = work / "compiler-build"
    stage = work / "stage"
    prefix = work / "sdk"
    run(args.cmake, "-S", source / "compiler", "-B", suite, "-G", "Unix Makefiles",
        f"-DCMAKE_C_COMPILER={args.cc}", f"-DCMAKE_CXX_COMPILER={args.cxx}",
        "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON",
        f"-DCWHIP_STAGE_PREFIX={stage}", f"-DCMAKE_INSTALL_PREFIX={prefix}",
        "-DCMAKE_INSTALL_LIBDIR=lib", "-DCMAKE_INSTALL_BINDIR=bin",
        "-DCMAKE_INSTALL_INCLUDEDIR=include", "-DCMAKE_INSTALL_DATADIR=share",
        f"-DCWHIP_CLANG_EXECUTABLE={args.clang}",
        f"-DCWHIP_GTK={args.gtk}", f"-DCWHIP_GTK_SOURCEVIEW={args.sourceview}",
        f"-DCWHIP_GTK_TESTS={'ON' if headless else 'OFF'}")
    run(args.cmake, "--build", suite, "--parallel", "4", "--target", "cwhip",
        "cwhip_tests", "cwhip_command_line_tests", "cwhip_gc_runtime_tests")

    run(args.cmake, "--install", suite)
    app_suites = []
    for name, enabled in (("editor", args.editor), ("debugger", args.debugger)):
        if not sourceview or enabled != "ON":
            print(f"EXCLUDED: standalone {name} (disabled or GUI SDK unavailable)", flush=True)
            continue
        app_build = work / name
        internal_tests = ()
        if name == "debugger":
            internal_tests = (f"-DCDBG_RUNTIME_SOURCE={source / 'compiler/src/RuntimeGc.c'}",)
            print("INCLUDED: compiler-private runtime source-line stepping in umbrella "
                  "integration only; standalone debugger does not require runtime sources.", flush=True)
        run(args.cmake, "-S", source / name, "-B", app_build, "-G", "Unix Makefiles",
            f"-DCMAKE_PREFIX_PATH={prefix}", f"-DCMAKE_C_COMPILER={args.cc}",
            f"-DCwhip_DIR={prefix / 'lib/cmake/Cwhip'}",
            "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON", *internal_tests)
        run(args.cmake, "--build", app_build, "--parallel", "4")
        app_suites.append((name, app_build, ()))
    failures = []
    # Run every suite even if an earlier suite fails, then propagate failure.
    suites = [
        ("compiler", suite, ("--exclude-regex", r"^(cedit_|cdbg_|cwhip_example_editor_)")),
        *app_suites,
        ("workspace", build, ()),
    ]
    print("EXCLUDED from compiler CTest: integrated cedit_*, cdbg_* and "
          "cwhip_example_editor_* (monorepo copies). Standalone component-owned suites replace them. "
          "Fuzz/sanitizer/coverage instrumentation is not enabled by this target.", flush=True)
    print("Website has no standalone test runner; workspace tests cover its real "
          "Markdown/assets/manifest adapter.", flush=True)
    for name, directory, extra in suites:
        try:
            run(args.ctest, "--test-dir", directory, "--output-on-failure",
                "--parallel", "1", *extra)
        except subprocess.CalledProcessError:
            failures.append(name)
    try:
        run(sys.executable, source / "tests/sdk_checks.py", "--prefix", prefix,
            "--cmake", args.cmake, "--ctest", args.ctest, "--apps", "OFF")
    except subprocess.CalledProcessError:
        failures.append("relocated SDK external-project contract")
    if failures:
        raise RuntimeError("test-all failed suites: " + ", ".join(failures))
    print("test-all passed: compiler + standalone applications + workspace + relocated SDK", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f"test-all: {error}")
