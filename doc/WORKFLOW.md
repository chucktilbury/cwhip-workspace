# Workspace workflow

This umbrella records a tested selection of component revisions, not copies of
their source. The Git links in each workspace commit are the source of truth.
The [top-level CMake build](BUILD.md) bootstraps the compiler and external apps
with a private binary-tree stage. There is no unified install, release, or
upload command here.

## Clone and restore pinned revisions

Git is required for the workspace. Python 3.11 or newer is required for builds
and tests; Python 3 also runs the optional status helper. Clone all component
repositories with:

```sh
git clone --recurse-submodules https://github.com/chucktilbury/cwhip-workspace.git
cd cwhip-workspace
```

For an existing clone, or after checking out or pulling a workspace revision:

```sh
git submodule sync --recursive
git submodule update --init --recursive
```

These commands restore the revisions selected by the workspace, not the newest
component branch tips. Inspect and commit or otherwise preserve local work
before changing revisions; do not use force to discard component changes.
Ordinary builds must not run `git submodule update --remote`.

The initial selection is:

| Path | Repository branch for deliberate updates | Pinned commit |
| --- | --- | --- |
| `compiler` | `chucktilbury/cwhip`, `master` | `5a229c632a1bddd01891c0ef0776f37e34ab8290` |
| `editor` | `chucktilbury/cedit`, `main` | `cf3a85e931c7c3df8ed3434db320f86b99ebc912` |
| `debugger` | `chucktilbury/cdbg`, `main` | `ea7d715eff3ce0d0cba45c143bb86d7d667358dd` |
| `website` | `chucktilbury/cwhip-website`, `main` | `fca61b480e03ac6b4d610995b8a603286f6771ff` |

This table describes the seed, not future updates; inspect the current Git
links with `git ls-tree HEAD compiler editor debugger website`. The `branch`
fields in `.gitmodules` guide explicit remote updates only. They do not make
normal initialization or builds follow those branches automatically.

## Develop and update components deliberately

Submodule initialization normally leaves each component at a **detached HEAD**:
a specific commit rather than a local branch. This is expected for reproducible
checkouts. Before editing, create a branch in the relevant component, based on
the pin. For example, from the workspace root:

```sh
git -C editor switch -c my-editor-change
# Edit and review files inside editor/.
git -C editor add src/cedit.cw
git -C editor commit -m "Describe editor change"
git -C editor push -u origin my-editor-change
# Complete the component's review/merge process before selecting its final pin.
```

There are two independent levels of commits: first commit and push component
work to its owning repository; then select the final published component
revision and commit the updated Git link in this repository. A workspace
commit does not upload component commits. Never record a component commit
that collaborators cannot fetch from the component remote.

To deliberately advance a component to its configured upstream branch tip,
start with clean component and workspace checkouts, then explicitly run:

```sh
git submodule update --init --remote --checkout editor
git -C editor log -1 --oneline
git diff --submodule=log -- editor
# Run the component's relevant checks and any dependent integration checks.
git add editor
git diff --cached --submodule=log
git commit -m "Update editor revision"
git push origin HEAD
```

Alternatively, fetch and check out a reviewed exact commit in the component,
then stage its path in the umbrella. Update only the components intended for
the change. Review dependency compatibility before advancing pins. Detached
HEAD is suitable for selecting a pin; create a branch before new development
so commits are not left reachable only through the local reflog.

## Dependency and setup plan

Track work in the
[Cwhip Applications project](https://github.com/users/chucktilbury/projects/1).
Each stage has an explicit handoff; the umbrella does not claim these stages
are complete merely because all submodules clone.

### 1. Compiler SDK

The compiler owns the compiler/runtime, public headers and runtime archives,
standard modules/packages, shared GTK/GtkSourceView bindings, and their APIs.
Its existing build and install instructions are in
[`compiler/README.md`](../compiler/README.md) and
[`compiler/doc/INSTALLATION.md`](../compiler/doc/INSTALLATION.md).
They require CMake, a C11/C++17 toolchain, Clang on PATH, POSIX facilities, and
Python 3.11 or newer for package tooling. Optional GUI dependencies are
documented there; this workspace does not install system packages.

Use [BUILD.md](BUILD.md) for the verified umbrella bootstrap, which configures
the pinned compiler in `build/compiler-build` with `build/stage` as its private
resource prefix. It does not run the compiler's install script. A supported,
versioned SDK for external applications remains work in
[chucktilbury/cwhip#1](https://github.com/chucktilbury/cwhip/issues/1).
Acceptance includes a clean install prefix with no source-tree assumptions
and documented compatible versions. Do not treat today's integrated application
targets as proof that the external repositories can build independently.

### 2. External applications

After the SDK boundary is established, build `cedit` and `cdbg` against a clean
installed prefix, with standalone tests/CI, installation, packaging, and an
explicit compiler compatibility policy:

- [chucktilbury/cedit#1](https://github.com/chucktilbury/cedit/issues/1)
- [chucktilbury/cdbg#1](https://github.com/chucktilbury/cdbg/issues/1)

The pinned external application repositories have **no standalone build
scripts of their own**. Their current
[`editor/README.md`](../editor/README.md) and
[`debugger/README.md`](../debugger/README.md) refer to the compiler's integrated
prototype workflows. Those build the copies still in the compiler repository,
not these external submodules. The umbrella instead reuses that build logic
with `editor/src` and `debugger/src`, including the launcher, terminal native
helper and embedded inspector. This is temporary in-tree SDK coupling, not
completion of standalone SDK or release packaging. GTK 4 >= 4.10 and
GtkSourceView 5 are application dependencies; `cdbg`
also needs GDB, and its value inspector needs Python-enabled GDB with
`gdb.MICommand`. Compiling `.cw` debugger targets needs Cwhip.

### 3. Automated documentation generation

Once component inputs and their interfaces are established, assemble
documentation from the selected component revisions in a separate staging
area, preserving source ownership. Generate API inputs from compiler-produced
function headers and DOT outputs; make Markdown collection, Doxygen/Graphviz
requirements, links, and resulting artifacts reproducible:

- [chucktilbury/cwhip#2](https://github.com/chucktilbury/cwhip/issues/2)
- [chucktilbury/cwhip-website#1](https://github.com/chucktilbury/cwhip-website/issues/1)

The pinned `website/build.py` expects to run from the site directory and looks
for documentation Markdown in its **parent** plus `content/`. The umbrella
layout does not satisfy the old parent-directory assumption directly. The
workspace's explicit `website` target now stages `compiler/doc/*.md` and
`website/content/` under the binary directory before running the pinned
generator. It generates fresh real Markdown pages, CSS, JavaScript and the
manifest-driven docs index; it does not copy a prebuilt site. The pinned
Doxygen ZIP contains no HTML. By default the target diagnoses this and omits
the API index link; an existing HTML reference may be supplied explicitly
with `CWHIP_WEBSITE_API_HTML`. Fresh API generation and comprehensive
cross-repository link validation remain future work. See [BUILD.md](BUILD.md).

### 4. MANUAL publication

Generation and publication are separate stages. Review the generated site
locally, check document/API links and asset completeness, then the owner
manually uploads the approved artifact to the hosting service. No ordinary
build, test, workspace setup, or CI job should deploy or require hosting
credentials. Do **not** execute `website/install.sh`: it performs an upload.
The publication handoff and review procedure remain part of
[chucktilbury/cwhip-website#1](https://github.com/chucktilbury/cwhip-website/issues/1).

## Workspace validation

From the workspace root:

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
python3 scripts/status.py
python3 -m unittest discover -s tests -v
git submodule status --recursive
git status --short
```

The read-only helper prints the committed pin and actual checkout for each
component. It exits nonzero for an uninitialized, dirty (including untracked
files), or mismatched component, or a Git error. It performs no fetch,
initialization, build, or upload. Pins come from workspace `HEAD`, so a staged
Git-link update still reports a mismatch until it is committed. It does not
replace component tests or check SDK/API compatibility. CTest also runs the
diagnostic unit tests, website adapter tests, compilation smoke, native
terminal test, MI parser, embedded inspector and no-op build checks.
[BUILD.md](BUILD.md#validation) lists the opt-in timestamp/dependency probes.

For independent clone validation, clone this repository into a fresh directory
with `--recurse-submodules`, compare `git ls-tree HEAD` and
`git submodule status --recursive` with the selected workspace revision, run
the helper, and confirm `git status --short` is empty. All four component
directories must contain tracked source files at exactly the committed hashes.

## Licensing

No new license or reuse grant is introduced by the umbrella. The compiler and
application split's licensing choice is unresolved in
[chucktilbury/cwhip#3](https://github.com/chucktilbury/cwhip/issues/3).
Public repository visibility alone does not grant reuse or redistribution
rights. Confirm an explicit licensing policy with the owner before inviting
external contributions or promising such rights.
