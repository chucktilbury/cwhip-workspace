#!/usr/bin/env python3
"""Report committed pins and local component state without changing anything."""

from pathlib import Path
import argparse
import subprocess
import sys


COMPONENTS = ("compiler", "editor", "debugger", "website")


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Report local edits without failing; still require exact HEAD pins")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    failed = False
    mismatched = []
    uninitialized = []
    try:
        for name in COMPONENTS:
            entry = git(root, "ls-tree", "HEAD", "--", name).split()
            if len(entry) != 4 or entry[:2] != ["160000", "commit"]:
                raise ValueError(f"{name}: HEAD does not contain a component Git link")
            pin = entry[2]
            component = root / name
            if not (component / ".git").exists():
                print(f"{name}: pinned={pin} current=- UNINITIALIZED")
                uninitialized.append(name)
                failed = True
                continue
            current = git(component, "rev-parse", "HEAD")
            states = []
            if current != pin:
                states.append("MISMATCH")
                mismatched.append(name)
            if git(component, "status", "--porcelain", "--untracked-files=all",
                   "--ignore-submodules=none"):
                states.append("DIRTY")
            print(f"{name}: pinned={pin} current={current} {' '.join(states) or 'OK'}")
            failed |= "MISMATCH" in states or ("DIRTY" in states and not args.allow_dirty)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"status: {detail}", file=sys.stderr)
        return 1
    if mismatched:
        names = " ".join(mismatched)
        print(f"\nPin MISMATCH: {names}. Pins are read from workspace HEAD, not the index.")
        print("If these commits are intended, first ensure the component commits are pushed "
              "to their remotes. Then, from the workspace root, review and record the pins:")
        print(f"  git add {names}")
        print("  git diff --cached --submodule=log")
        print('  git commit -m "Update component pins"')
        print("  git push")
        print("Otherwise, preserve any local component work, then restore the committed pins:")
        print(f"  git submodule update --init --checkout {names}")
    if uninitialized:
        print("\nInitialize the committed component pins from the workspace root:")
        print(f"  git submodule update --init --checkout {' '.join(uninitialized)}")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
