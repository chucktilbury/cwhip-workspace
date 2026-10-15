"""Remove one workspace build's generated products and owned publication links."""

import argparse
from pathlib import Path
import shutil


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def clean(build: Path, public_bin: Path) -> None:
    build = build.resolve()
    stage = build / "stage"
    for name in ("cwhip", "cwhip-pkg", "cedit", "cedit.bin", "cdbg"):
        link = public_bin / name
        if link.is_symlink() and link.readlink() == stage / "bin" / name:
            link.unlink()
    for name in ("stage", "compiler-stage", "tests", "website", "Testing", "test-all"):
        remove(build / name)
    # Retire native targets from the previous umbrella-owned application build.
    for name in ("cedit_launcher", "cdbg_terminal"):
        remove(build / "CMakeFiles" / (name + ".dir"))
    apps = build / "apps"
    for app in ("cedit", "cdbg"):
        remove(apps / app)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--public-bin", type=Path, required=True)
    args = parser.parse_args()
    try:
        clean(args.build, args.public_bin)
    except OSError as error:
        parser.exit(1, f"Workspace clean: {error}\n")


if __name__ == "__main__":
    main()
