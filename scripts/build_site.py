"""Run the pinned full-workspace website builder without publishing."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def build(workspace: Path, work: Path, api_html: Path | None) -> None:
    workspace, work = workspace.resolve(), work.resolve()
    if workspace == work or work in workspace.parents:
        raise ValueError("Website staging must be separate from the workspace root")

    doc_stage = (work / "doc").resolve()
    protected_paths = [
        *(workspace / name for name in ("compiler", "editor", "debugger", "cmacros", "website")),
        workspace / "doc",
    ]
    protected_paths = [path.resolve() for path in protected_paths]
    staging_paths = (work, doc_stage)
    for staging_path in staging_paths:
        for protected_path in protected_paths:
            if (staging_path == protected_path
                    or staging_path in protected_path.parents
                    or protected_path in staging_path.parents):
                raise ValueError(
                    f"Website staging path overlaps protected workspace input: {staging_path}"
                )

    required = (
        "website/build.py",
        "website/check_site.py",
        "compiler/doc/GETTING_STARTED.md",
        "editor/CEDIT.md",
        "debugger/CDBG.md",
        "cmacros/README.md",
        "cmacros/doc/BUILD.md",
        "cmacros/doc/LANGUAGE.md",
        "cmacros/doc/DIAGNOSTICS.md",
        "cmacros/examples/README.md",
        "doc/FIRST-PROGRAM.md",
    )
    for name in required:
        if not (workspace / name).is_file():
            raise ValueError(f"Required workspace website input missing: {workspace / name}")

    if api_html is not None:
        api_html = api_html.resolve()
        if not (api_html / "index.html").is_file():
            raise ValueError(f"Doxygen HTML directory lacks index.html: {api_html}")
        if (api_html == doc_stage or doc_stage in api_html.parents
                or api_html in doc_stage.parents):
            raise ValueError("Doxygen input must be outside the recreated doc staging directory")

    if doc_stage.exists():
        shutil.rmtree(doc_stage)
    output = doc_stage / "website" / "site"
    command = [
        sys.executable,
        str(workspace / "website/build.py"),
        "--workspace", str(workspace),
        "--output-dir", str(output),
    ]
    subprocess.run(command, cwd=workspace / "website", check=True)
    if api_html is not None:
        shutil.copytree(api_html, output / "html")
    print(f"Generated site: {output} (WEBSITE UPLOAD MANUAL)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--api-html", default="")
    args = parser.parse_args()
    try:
        build(args.workspace, args.work, Path(args.api_html) if args.api_html else None)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"website: {error}\n")


if __name__ == "__main__":
    main()
