"""Explicit destructive-to-products regression for the standard workspace clean."""

import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
NAMES = ("cwhip", "cwhip-pkg", "cmacros", "cedit", "cedit.bin", "cdbg")


def command(*args):
    subprocess.run([str(arg) for arg in args], check=True, cwd=ROOT)


def links():
    return {name: (ROOT / "bin" / name).readlink()
            for name in NAMES if (ROOT / "bin" / name).is_symlink()}


def assert_clean(build):
    for name in ("stage", "compiler-stage", "tests", "website", "Testing", "test-all"):
        assert not (build / name).exists(), build / name
    for app in ("cmacros", "cedit", "cdbg"):
        project = build / "apps" / app
        assert not project.exists(), project
    assert not list((build / "compiler-build").rglob("*.o")), "Nested compiler objects survived"
    assert not list((build / "CMakeFiles").rglob("*.o")), "Root native objects survived"
    for name in ("CMakeCache.txt", "Makefile", "compiler-build/CMakeCache.txt",
                 "compiler-build/Makefile"):
        assert (build / name).is_file(), f"Configure state lost: {name}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--active-build", type=Path)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--ctest", default="ctest")
    args = parser.parse_args()
    build = args.build.resolve()
    command(args.cmake, "--build", build, "--parallel", "4")
    command(args.cmake, "--build", build, "--target", "website")
    command(args.ctest, "--test-dir", build, "--output-on-failure")
    assert (build / "website/doc/website/site/index.html").is_file()
    assert list((build / "compiler-build").rglob("*.o"))
    for _ in range(2):
        command(args.cmake, "--build", build, "--target", "clean", "--parallel", "4")
        assert_clean(build)
        assert not any(str(build / "stage") in str(target) for target in links().values())
    command(args.cmake, "--build", build, "--parallel", "4")
    command(args.ctest, "--test-dir", build, "--output-on-failure")
    command(args.cmake, "--build", build, "--target", "website")
    command(args.cmake, "--build", build, "--clean-first", "--parallel", "4")
    assert not (build / "website").exists(), "Opt-in website must be removed by clean-first"
    command(args.ctest, "--test-dir", build, "--output-on-failure")
    if args.active_build:
        active = args.active_build.resolve()
        assert active != build
        command(args.cmake, "--build", active, "--parallel", "4")
        before = links()
        assert before
        artifacts = {path: path.stat().st_mtime_ns
                     for path in (active / "stage").rglob("*") if path.is_file()}
        command(args.cmake, "--build", build, "--target", "clean", "--parallel", "4")
        assert_clean(build)
        assert links() == before, "Inactive clean removed active publication links"
        assert all(path.stat().st_mtime_ns == stamp for path, stamp in artifacts.items())
        command(args.ctest, "--test-dir", active, "--output-on-failure")
    print(f"Standard clean regression passed: {build}")


if __name__ == "__main__":
    main()
