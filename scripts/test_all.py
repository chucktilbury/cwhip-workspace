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
    work = build / "test-all"
    work.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("CWHIP_") and key not in
           ("DESTDIR", "CC", "DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
            "MAKEFLAGS", "MFLAGS", "MAKELEVEL", "CTEST_PARALLEL_LEVEL")}
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "xdg")):
        path = work / name
        path.mkdir(exist_ok=True)
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
    run(args.cmake, "-S", source / "compiler", "-B", suite, "-G", "Unix Makefiles",
        f"-DCMAKE_C_COMPILER={args.cc}", f"-DCMAKE_CXX_COMPILER={args.cxx}",
        "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON",
        f"-DCWHIP_STAGE_PREFIX={stage}", f"-DCMAKE_INSTALL_PREFIX={stage}",
        "-DCMAKE_INSTALL_LIBDIR=lib", "-DCMAKE_INSTALL_BINDIR=bin",
        "-DCMAKE_INSTALL_INCLUDEDIR=include", "-DCMAKE_INSTALL_DATADIR=share",
        f"-DCWHIP_CLANG_EXECUTABLE={args.clang}",
        f"-DCWHIP_GTK={args.gtk}", f"-DCWHIP_GTK_SOURCEVIEW={args.sourceview}",
        f"-DCWHIP_GTK_TESTS={'ON' if headless else 'OFF'}")
    run(args.cmake, "--build", suite, "--parallel", "4", "--target", "cwhip",
        "cwhip_tests", "cwhip_command_line_tests", "cwhip_gc_runtime_tests")

    # Split app runners assume compiler-monorepo fixture locations. Assemble
    # only the layout they need without substituting integrated app sources.
    adapter = work / "external-inputs"
    if adapter.exists():
        shutil.rmtree(adapter)
    adapter.mkdir()
    shutil.copytree(source / "editor/tests", adapter / "editor-tests")
    shutil.copytree(source / "compiler/examples", adapter / "examples")
    shutil.rmtree(adapter / "examples/editor")
    shutil.copytree(source / "editor/src", adapter / "examples/editor")
    for name in ("editor_dialog_fixture.c", "project_explorer_fixture.c", "cwhip_project_fixture.c"):
        shutil.copy2(source / "compiler/tests" / name, adapter / "editor-tests" / name)
    shutil.copytree(source / "debugger/tests", adapter / "tests")
    shutil.copytree(source / "debugger/src", adapter / "tools/cdbg")
    (adapter / "src").mkdir()
    shutil.copy2(source / "compiler/src/RuntimeGc.c", adapter / "src/RuntimeGc.c")
    (adapter / "include").symlink_to(stage / "include", target_is_directory=True)

    external = work / "external-build"
    run(args.cmake, "-S", source / "cmake/test-all", "-B", external,
        "-G", "Unix Makefiles", f"-DWORKSPACE_SOURCE={source}",
        f"-DWORKSPACE_BUILD={build}", f"-DCOMPILER_STAGE={stage}",
        f"-DADAPTER={adapter}", f"-DCLANG={args.clang}",
        f"-DHEADLESS={'ON' if headless and sourceview else 'OFF'}",
        f"-DEDITOR={args.editor if sourceview else 'OFF'}",
        f"-DDEBUGGER={args.debugger if sourceview else 'OFF'}")
    failures = []
    # Run every suite even if an earlier suite fails, then propagate failure.
    suites = (
        ("compiler", suite, ("--exclude-regex", r"^(cedit_|cdbg_|cwhip_example_editor_)")),
        ("external apps", external, ()),
        ("workspace", build, ()),
    )
    print("EXCLUDED from compiler CTest: integrated cedit_*, cdbg_* and "
          "cwhip_example_editor_* (monorepo copies). External app runners replace them. "
          "Fuzz/sanitizer/coverage instrumentation is not enabled by this target.", flush=True)
    print("Website has no standalone test runner; workspace tests cover its real "
          "Markdown/assets/manifest adapter.", flush=True)
    for name, directory, extra in suites:
        try:
            run(args.ctest, "--test-dir", directory, "--output-on-failure",
                "--parallel", "1", *extra)
        except subprocess.CalledProcessError:
            failures.append(name)
    if failures:
        raise RuntimeError("test-all failed suites: " + ", ".join(failures))
    print("test-all passed: compiler + external applications + workspace", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f"test-all: {error}")
