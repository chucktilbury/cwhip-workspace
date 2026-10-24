# Workspace workflow

This umbrella records a tested selection of component revisions, not copies of
their source. The Git links in each workspace commit are the source of truth.
The [top-level CMake build](BUILD.md) builds/installs the compiler SDK, then
configures standalone applications against that private installed prefix.
There is no unified public release or upload command here.
For installing and using Cwhip rather than developing the components, follow
[the first-program source-install guide](FIRST-PROGRAM.md).

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

Inspect the current committed pins and initialized checkouts directly:

```sh
git ls-tree HEAD compiler editor debugger cmacros website
git submodule status --recursive
```

This avoids relying on a stale copy of the seed revisions. The `branch`
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

### Troubleshooting: pin MISMATCH

`workspace_diagnostics` compares each component checkout with the Git link in
the workspace's committed `HEAD`. `MISMATCH` after intentionally updating a
component is not a compiler/test failure: the workspace still records its old
revision. Staging the Git link alone does not resolve this check.

If the new commits are intended, first ensure they are pushed to their
component remotes so collaborators can fetch them. From the workspace root,
record only the mismatched components (replace `editor debugger` below with
the names reported by the diagnostic):

```sh
git add editor debugger
git diff --cached --submodule=log
git commit -m "Update component pins"
git push
```

Otherwise, preserve any local component work, then restore the committed pins:

```sh
git submodule update --init --checkout editor debugger
```

The same update command initializes components reported as `UNINITIALIZED`.
Rerun `ctest --test-dir build --output-on-failure -R '^workspace_diagnostics$'`
after resolving the pins. `--allow-dirty` permits local file edits, not pin
mismatches or uninitialized components; diagnostics never change checkouts.

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

Use [BUILD.md](BUILD.md) for the umbrella orchestration, which configures
the compiler in `build/compiler-build`, builds into `build/compiler-stage`,
and installs the whole SDK to `build/stage`. User-facing executables are published as maintained links in
workspace-root `bin/`; the last build selects the active private stage.
It uses CMake install, never the compiler's shell install script. The
exact-version installed contract is described in
[`compiler/doc/CMAKE-SDK.md`](../compiler/doc/CMAKE-SDK.md);
future compatibility/release work remains tracked in
[chucktilbury/cwhip#1](https://github.com/chucktilbury/cwhip/issues/1).
Acceptance includes a clean install prefix with no source-tree assumptions
and documented compatible versions. Do not treat today's integrated application
targets as proof that the external repositories can build independently.

### Numeric-v2 integration

The 0.0.2 `numeric-v2` SDK is source- and native-ABI-incompatible with 0.0.1.
This workspace integration depends on the compiler numeric execution migration
in [chucktilbury/cwhip#25](https://github.com/chucktilbury/cwhip/pull/25) and
the SDK and stdlib migration in
[chucktilbury/cwhip#26](https://github.com/chucktilbury/cwhip/pull/26), based on
#25. The standalone consumer migrations are
[chucktilbury/cedit#14](https://github.com/chucktilbury/cedit/pull/14),
[chucktilbury/cdbg#15](https://github.com/chucktilbury/cdbg/pull/15), and
[chucktilbury/cmacros#6](https://github.com/chucktilbury/cmacros/pull/6).
These PRs must land in dependency order before the workspace component pins can
select and validate the complete migration. Rebuild native packages and do not
mix SDK prefixes.

### 2. Standalone CLI and GUI applications

The standalone `cmacros` CLI builds against the installed Cwhip 0.0.2
`numeric-v2` SDK without GTK and is included in the default workspace build. Its upstream
project owns the implementation, examples, tests and MIT license:

- [chucktilbury/cmacros](https://github.com/chucktilbury/cmacros)

It is a standalone macro processor, not a required compiler preprocessing
stage. The workspace configures it against the staged SDK, installs its
executable into the shared stage, and runs its component-owned CTest suite.

The `cedit` and `cdbg` GUI projects build against a clean installed prefix,
with standalone tests/CI, installation, packaging, and an explicit compiler
compatibility policy:

- [chucktilbury/cedit#1](https://github.com/chucktilbury/cedit/issues/1)
- [chucktilbury/cdbg#1](https://github.com/chucktilbury/cdbg/issues/1)

Each application project owns an independent CMake/build/test/clean/install
interface and fixtures. See their
[`editor/doc/BUILD.md`](../editor/doc/BUILD.md) and
[`debugger/doc/BUILD.md`](../debugger/doc/BUILD.md). Configure either with
`-DCMAKE_PREFIX_PATH=/path/to/installed-sdk`; no compiler/workspace checkout
is required. The umbrella invokes those same interfaces, not the compiler's
integrated app duplicates. They remain proof-of-concept applications, and
packaging/CI/release compatibility beyond SDK 0.0.2 `numeric-v2` remains
separate work.
GTK 4 >= 4.10 and
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

The pinned `website/build.py` supports full-workspace input. The explicit
`website` target passes the workspace root and writes generated pages into the
binary tree; it includes cmacros guides and original example assets alongside
compiler, editor, debugger and workflow documentation. The site builder checks
required source pages and local links; it does not copy a prebuilt site.
Doxygen HTML is optional and can be supplied with `CWHIP_WEBSITE_API_HTML`.
Fresh API generation remains future work. See [BUILD.md](BUILD.md).

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
# All supported compiler, external app and workspace suites:
cmake --build build --target test-all
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
terminal test, MI parser and embedded inspector. Ordinary `make test` reuses
the completed build; `cmake --build build --target check-noop` explicitly
checks a second incremental build without making CTest rebuild the main tree.
[BUILD.md](BUILD.md#validation) lists the opt-in timestamp/dependency probes.
`test-all` includes headless isolated Xvfb/DBus app suites when dependencies
are available and prints exclusions for missing optional tools. It uses the
external app sources, not the compiler's duplicate apps.

The standard clean command now propagates through all generated component
products for that build:

```sh
cmake --build build --target clean
cmake --build build
# Equivalent clean-before-rebuild:
cmake --build build --clean-first
```

Nested compiler objects, the private SDK stage, app/test outputs, full-suite
trees and website staging are cleaned. Configure state remains for rebuilding.
Only root `bin/` links owned by this binary directory are removed; cleaning an
inactive configuration preserves active links and other build directories.
Recursive clean currently requires Unix Makefiles; unsupported generators
are rejected at configure time. See [BUILD.md](BUILD.md#clean).

For independent clone validation, clone this repository into a fresh directory
with `--recurse-submodules`, compare `git ls-tree HEAD` and
`git submodule status --recursive` with the selected workspace revision, run
the helper, and confirm `git status --short` is empty. All five component
directories must contain tracked source files at exactly the committed hashes.

## Licensing

No new license or reuse grant is introduced by the umbrella. cmacros is
MIT-licensed in its owning repository. The compiler and GUI application split's
licensing choice is unresolved in
[chucktilbury/cwhip#3](https://github.com/chucktilbury/cwhip/issues/3).
Public repository visibility alone does not grant reuse or redistribution
rights. Confirm an explicit licensing policy with the owner before inviting
external contributions or promising such rights.
