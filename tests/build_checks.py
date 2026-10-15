"""Focused post-build checks; dependency probing is explicit, not a default CTest."""

import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def run(command, work, env=None):
    if env is None:
        env = {key: value for key, value in os.environ.items()
               if key not in ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")}
    result = subprocess.run([str(item) for item in command], cwd=work, env=env,
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise AssertionError(f"{command}\n{result.stdout}\n{result.stderr}")
    return result


def environment(work):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("CWHIP_") and k not in ("CC", "DESTDIR")}
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "xdg"),
                      ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"),
                      ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        directory = work / name
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        env[key] = str(directory)
    return env


def outputs(build):
    stage = build / "stage"
    paths = [stage / "bin/cwhip", stage / "lib/cwhip/libcwhip_runtime.a",
             build / "compiler-build/src/cwhip-resources.stamp"]
    for name in ("cedit", "cedit.bin", "cdbg"):
        path = stage / "bin" / name
        if path.exists():
            paths.append(path)
    paths.extend((build / "apps").glob("*/*-project/cwhip-pkg.*"))
    paths.extend(stage.glob("share/cwhip/modules/*/*/lib/*.a"))
    result = {path: path.stat().st_mtime_ns for path in paths}
    for path in (ROOT / "bin").iterdir():
        if path.is_symlink():
            result[path] = (path.lstat().st_mtime_ns, str(path.readlink()))
    return result


def constants():
    tree = ast.parse((ROOT / "debugger/tests/test_cdbg.py").read_text())
    return {node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in ("VALUES_FIXTURE", "VALUE_CHECKS")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "inspector", "noop", "dependencies"), required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--clang", default="clang")
    args = parser.parse_args()
    build = args.build.resolve()
    work = build / "tests" / args.mode
    work.mkdir(parents=True, exist_ok=True)
    compiler = ROOT / "bin/cwhip"
    env = environment(work)
    command = [args.cmake, "--build", build]
    if args.mode == "noop":
        before = outputs(build)
        run(command, work)
        assert before == outputs(build), "An unchanged build rewrote compiler, apps, packages or resources"
    elif args.mode == "dependencies":
        # Restore source timestamps even on failure; never edit component contents.
        probes = [
            (ROOT / "editor/src/cedit.cw", "cedit.bin"),
            (ROOT / "editor/src/launcher.c", "cedit"),
            (ROOT / "debugger/src/mi.cw", "cdbg"),
            (ROOT / "debugger/src/terminal.cw", "cdbg"),
            (ROOT / "debugger/src/terminal.c", "cdbg"),
            (ROOT / "debugger/src/values.py", "cdbg"),
            (ROOT / "debugger/src/embed_values.py", "cdbg"),
            (ROOT / "compiler/include/cwhip/RuntimeGc.h", "cdbg"),
            (ROOT / "compiler/stdlib/gtk/0.1.0/cwhip-package.toml", "cdbg"),
            (build / "compiler-stage/share/cwhip/modules/gtk/0.1.0/lib/libcwhip_gtk.a", "cdbg"),
            (build / "compiler-stage/share/cwhip/modules/sqlite/0.1.0/lib/libcwhip_sqlite.a", "cedit.bin"),
            (build / "compiler-stage/lib/cwhip/libcwhip_runtime.a", "cdbg"),
        ]
        for source, name in probes:
            output = build / "stage/bin" / name
            before = output.stat().st_mtime_ns
            original = source.stat()
            time.sleep(0.05)
            try:
                source.touch()
                run(command, work)
                assert output.stat().st_mtime_ns > before, f"{source} did not rebuild {name}"
                assert (ROOT / "bin" / name).resolve() == output.resolve()
                assert (ROOT / "bin" / name).stat().st_mtime_ns == output.stat().st_mtime_ns
            finally:
                os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
            print(f"Dependency rebuilt {name}: {source}")
        run(command, work)
        before = outputs(build)
        run(command, work)
        assert before == outputs(build), "Dependency probes did not settle to a no-op"
    elif args.mode == "smoke":
        assert compiler.readlink() == build / "stage/bin/cwhip"
        package_tool = ROOT / "bin/cwhip-pkg"
        with tempfile.TemporaryDirectory(dir=work, prefix="package-") as package:
            run([sys.executable, package_tool, "init", package], work, env)
        source = work / "hello.cw"
        source.write_text('start { print("workspace-smoke") }\n')
        binary = work / "hello"
        run([compiler, source, "-o", binary], work, env)
        result = run([binary], work, env)
        assert result.stdout == "workspace-smoke" and not result.stderr, result
        cdbg = ROOT / "bin/cdbg"
        launcher = ROOT / "bin/cedit"
        if launcher.exists():
            assert launcher.resolve().parent == (ROOT / "bin/cedit.bin").resolve().parent
            # Exercise the actual published launcher bytes with a harmless
            # sibling, not an application GUI.
            with tempfile.TemporaryDirectory(dir=work, prefix="launcher-") as directory:
                launcher_work = Path(directory)
                shutil.copy2(launcher, launcher_work / "cedit")
                sibling = launcher_work / "cedit.bin"
                sibling.write_text("#!/bin/sh\nprintf 'launcher-sibling-ok'\n")
                sibling.chmod(0o755)
                result = run([launcher_work / "cedit", "--foreground"], work, env)
                assert result.stdout == "launcher-sibling-ok", result
        if cdbg.exists():
            result = run([cdbg, "--help"], work, env)
            assert "Usage: cdbg" in result.stdout and not result.stderr, result
        # Check the exact embedded inspector bytes, not just header existence.
        headers = [build / "tests/values.h"]
        app_header = build / "apps/cdbg/values.h"
        if cdbg.exists():
            headers.append(app_header)
        for header in headers:
            literals = header.read_text().split("=\n", 1)[1].removesuffix(";\n")
            embedded = "".join(json.loads(line) for line in literals.splitlines())
            assert embedded == (ROOT / "debugger/src/values.py").read_text(), header
    else:
        gdb = shutil.which("gdb")
        if not gdb:
            print("GDB absent: inspector execution requires Python-enabled GDB with gdb.MICommand")
            sys.exit(77)
        data = constants()
        source = work / "values.cw"
        source.write_text(data["VALUES_FIXTURE"])
        binary = work / "values"
        # Runtime-private DWARF types are required by the inspector. Give this
        # fixture a debug runtime even when the staged compiler is a Release build.
        runtime = work / "runtime-debug.o"
        run([args.clang, "-g", "-c", ROOT / "compiler/src/RuntimeGc.c",
             "-I", build / "stage/include", "-o", runtime], work, env)
        run([compiler, source, "-g", "-o", binary, runtime], work, env)
        checks = work / "checks.py"
        checks.write_text("SCRIPT = " + repr(str(ROOT / "debugger/src/values.py")) +
                          "\n" + data["VALUE_CHECKS"])
        # GDB reads its source argument as a command, including quote characters.
        result = run([gdb, "-q", "-nx", "--batch", binary,
                      "-ex", "set host-charset UTF-8",
                      "-ex", f"break {source}:19", "-ex", "run",
                      "-ex", f"source {checks}"], work, env)
        assert "VALUE_CHECKS_PASS" in result.stdout, result
    print(f"Workspace {args.mode} checks passed")


if __name__ == "__main__":
    main()
