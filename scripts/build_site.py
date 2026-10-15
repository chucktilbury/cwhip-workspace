"""Run the pinned cwd-relative generator on binary-tree staging, never publish."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys


def build(compiler_doc: Path, website: Path, work: Path, api_html: Path | None) -> None:
    compiler_doc, website, work = (p.resolve() for p in (compiler_doc, website, work))
    if any(work == source or work in source.parents or source in work.parents
           for source in (compiler_doc, website)):
        raise ValueError("Website staging must be separate from source directories")
    documents = list(compiler_doc.glob("*.md"))
    if not documents:
        raise ValueError(f"No compiler Markdown documentation in {compiler_doc}")
    for name in ("build.py", "content/docs.md", "content/styles.css", "content/app.js"):
        if not (website / name).is_file():
            raise ValueError(f"Required website input missing: {website / name}")
    if api_html is not None:
        api_html = api_html.resolve()
        if not (api_html / "index.html").is_file():
            raise ValueError(f"Doxygen HTML directory lacks index.html: {api_html}")
        if api_html == work / "doc" or work / "doc" in api_html.parents:
            raise ValueError("Doxygen input must be outside the recreated doc staging directory")
    # Recreate only this adapter's named staging directories, removing stale pages.
    doc_stage = work / "doc"
    if doc_stage.exists():
        shutil.rmtree(doc_stage)
    site_stage = doc_stage / "website"
    site_stage.mkdir(parents=True)
    for document in documents:
        shutil.copy2(document, doc_stage / document.name)
    shutil.copy2(website / "build.py", site_stage / "build.py")
    shutil.copytree(website / "content", site_stage / "content")
    manifest = site_stage / "content/docs.md"
    text = manifest.read_text()
    available = {p.name for p in documents} | {
        p.name for p in (site_stage / "content").glob("*.md") if p.name != "docs.md"
    }
    for href in re.findall(r"^-\s*\[[^\]]+\]\(([^)]+)\)", text, re.MULTILINE):
        if href.endswith(".md") and Path(href).name not in available:
            raise ValueError(f"Website manifest has no Markdown input for {href}")
        if not href.endswith(".md") and href != "./html/index.html":
            raise ValueError(f"Unsupported website manifest input: {href}")
    if api_html is None:
        text = re.sub(r"^-\s*\[[^\]]+\]\(\./html/index\.html\)\n?", "", text, flags=re.MULTILINE)
        print("Doxygen API HTML unavailable: omitting API reference from docs index. "
              "The pinned ZIP contains no HTML. Supply -DCWHIP_WEBSITE_API_HTML=/path/to/html "
              "to include an existing reference; API generation is not performed.", file=sys.stderr)
    manifest.write_text(text)
    subprocess.run([sys.executable, str(site_stage / "build.py")],
                   cwd=site_stage, check=True)
    if api_html is not None:
        shutil.copytree(api_html, site_stage / "site/html")
    print(f"Generated site: {site_stage / 'site'} (WEBSITE UPLOAD MANUAL)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler-doc", type=Path, required=True)
    parser.add_argument("--website", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--api-html", default="")
    args = parser.parse_args()
    try:
        build(args.compiler_doc, args.website, args.work,
              Path(args.api_html) if args.api_html else None)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"website: {error}\n")


if __name__ == "__main__":
    main()
