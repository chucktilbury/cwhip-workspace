"""Publish build executables without relocating their private resource prefix."""

import argparse
import os
from pathlib import Path


NAMES = ("cwhip", "cwhip-pkg", "cmacros", "cedit", "cedit.bin", "cdbg")


def publish(stage: Path, output: Path, names: list[str], enabled: list[str]) -> None:
    stage = stage.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        link = output / name
        target = stage / "bin" / name
        if link.exists() and not link.is_symlink():
            raise ValueError(f"Refusing to replace non-symlink executable: {link}")
        if name not in names:
            if link.is_symlink() and (name not in enabled or link.readlink() != target):
                link.unlink()
            continue
        if not target.is_file() or not os.access(target, os.X_OK):
            raise ValueError(f"Built executable missing or not executable: {target}")
        if link.is_symlink() and link.readlink() == target:
            continue
        temporary = output / f".{name}.{os.getpid()}.tmp"
        try:
            temporary.symlink_to(target)
            temporary.replace(link)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--names", nargs="+", choices=NAMES, required=True)
    parser.add_argument("--enabled", nargs="*", choices=NAMES, default=[])
    args = parser.parse_args()
    try:
        publish(args.stage, args.output, args.names, args.enabled)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Executable publication: {error}\n")


if __name__ == "__main__":
    main()
