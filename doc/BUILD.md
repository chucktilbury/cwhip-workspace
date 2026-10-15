# Workspace CMake build

## Prerequisites and default build

Initialize the selected revisions explicitly before configuring:

```sh
git submodule update --init --recursive
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Requirements: Linux/POSIX, CMake >= 3.24, a C11/C++17 toolchain, Clang on
PATH, Python >= 3.11 (standard library only), SQLite 3 development files,
and a single-config CMake generator. Unix Makefiles is verified; Ninja may
also be selected when installed. No package downloads or system installs
are performed. Use `-DCMAKE_BUILD_TYPE=Debug` for compiler/runtime debug
symbols, or `Release` for optimization. The compiler's normal default is
preserved when no build type is selected.

GTK 4 >= 4.10 and GtkSourceView 5 development packages are detected through
pkg-config. When both bindings are enabled, the default build includes the
editor and debugger from **editor/src** and **debugger/src**, not the duplicate
integrated application sources in the compiler checkout.

Named targets can be built separately:

```sh
cmake --build build --target cwhip
cmake --build build --target cedit cdbg
```

`cwhip` invokes the compiler's own incremental build before dependent apps.
It is intentionally visited on every workspace build to notice compiler,
runtime and package changes; unchanged files/binaries retain their timestamps.
`cmake --build build --parallel 4` is supported.

No configure/build/test updates submodules, accesses component remote tips,
runs an application GUI, deploys a website, or requires hosting credentials.
CTest invokes `cdbg --help` only, without creating a window. GUI launch and
interactive GDB debugging remain manual; using the debugger requires GDB,
and its value inspector requires Python-enabled GDB with `gdb.MICommand`.

## Options and custom paths

| Option | Default | Effect |
| --- | --- | --- |
| `CWHIP_GTK` | Detect GTK >= 4.10 | Compiler GTK bindings; explicit ON requires the development dependencies |
| `CWHIP_GTK_SOURCEVIEW` | Detect GtkSourceView with GTK enabled | SourceView bindings; requires `CWHIP_GTK=ON` |
| `CWHIP_BUILD_CEDIT` | ON | Include external editor when GUI bindings are enabled |
| `CWHIP_BUILD_CDBG` | ON | Include external debugger when GUI bindings are enabled |
| `BUILD_TESTING` | ON | Build the native helper test and register focused CTest checks |
| `CWHIP_WEBSITE_API_HTML` | Empty | Optional pre-generated Doxygen HTML directory containing `index.html` |

For a compiler-only build, explicitly disable both GUI bindings (including
when reconfiguring a directory previously configured with GUI enabled):

```sh
cmake -S . -B build-compiler -DCWHIP_GTK=OFF -DCWHIP_GTK_SOURCEVIEW=OFF
cmake --build build-compiler
ctest --test-dir build-compiler --output-on-failure
```

If GTK/SourceView is not detected, the compiler still builds by default.
Explicitly building an unavailable or disabled `cedit`/`cdbg` target fails
with an enable/dependency diagnostic, never a success-shaped no-op.
To keep the bindings but omit apps, set both `CWHIP_BUILD_CEDIT=OFF` and
`CWHIP_BUILD_CDBG=OFF`. Use separate binary directories for configurations.

Custom directories, including paths containing spaces, work:

```sh
cmake -S . -B "build custom"
cmake --build "build custom"
ctest --test-dir "build custom" --output-on-failure
```

In-source builds and binary directories inside a component are rejected.
`build*` directories immediately under the workspace are ignored by Git;
other custom binary directories should be outside the source tree.

## Outputs and SDK limitations

User-facing executables are available in **workspace-root `bin/`**:
`bin/cwhip`, `bin/cwhip-pkg`, `bin/cedit`, `bin/cedit.bin`, and `bin/cdbg`.
These are maintained absolute symlinks to the selected build's real executables.
The compiler resolves its real executable location and `cwhip-pkg` resolves
its script path, preserving private SDK discovery without environment wrappers.
The editor launcher resolves its real location and finds its `cedit.bin` sibling.

Each named build target republishes its executable links even on an otherwise
no-op build, repairing missing links without rewriting correct links. Rebuilt
binaries are immediately visible through the links; no stale executable copies
are kept. The compiler target switches compiler/package links and removes app
links from other builds or apps disabled in this configuration; successful app
targets then publish their own links. Non-symlink files with these names are
rejected rather than overwritten.

**Root `bin/` is shared: the last build selects the active configuration.**
Do not build or test different binary directories concurrently in one workspace.
Build the desired configuration before running its CTests. A compiler-only
build removes GUI links, and a compiler-only named target after switching builds
does not publish unbuilt apps. Configure alone does not change links.
Private `stage/bin/` binaries may remain after disabling an app but are not
published. Deleting/cleaning the active build can leave dangling links; build
again to restore them. Root links are intentionally not clean byproducts:
cleaning an inactive configuration must not delete another build's links.
This is not an install or relocatable release layout.

Intermediates, real executable files, copied resources and generated package
locks remain in the selected binary directory, here shown as `build/`:

| Path | Contents |
| --- | --- |
| `compiler-build/` | Separate compiler CMake configuration and object files |
| `stage/bin/` | `cwhip`, generated `cwhip-pkg`, `cedit` launcher, `cedit.bin`, `cdbg` |
| `stage/lib/cwhip/` | Runtime archive |
| `stage/include/cwhip/` | Staged runtime headers |
| `stage/share/cwhip/builtin/` | Builtin language sources |
| `stage/share/cwhip/modules/` | Standard packages, SQLite/GTK native archives, SourceView language resources |
| `apps/cedit/`, `apps/cdbg/` | Copied external sources, private HOME/XDG directories, package manifest and lock; debugger `values.h` |
| `tests/` | Focused test binaries, fixtures and isolated configuration |
| `website/doc/website/site/` | Explicitly generated site |

Application builds use the staged compiler's package discovery and
`cwhip-pkg init` to lock the standard packages. Runtime/include/builtin/module
paths are set to the private stage, legacy and user module overrides are
cleared, and HOME/XDG configuration is isolated per app. No user package
configuration is imported. Changes to native archives, SDK headers/resources,
package manifests, app sources, launcher, terminal helper and inspector/embed
scripts participate in incremental dependencies. Source copies are refreshed
when rebuilding an app, so removed files cannot linger in its staged sources.

This is a **temporary in-tree SDK bootstrap**, not an independently consumable
SDK or release/install packaging. The workspace uses the compiler's private
resource layout, native archive names, package implementation and C headers.
GTK native code still knows the compiler source language-resource path in
addition to the private stage's install-resource path. Keep the pinned source
checkouts and build directory available; moving/releasing this stage is not
promised. App options changed in an existing directory may leave old binaries
in the stage, but their named targets still fail when disabled. Use a new
binary directory for a pristine output set.

The compiler's integrated apps, website, install scripts and full test suites
are not built/run by the workspace bootstrap. No component or compiler behavior
is patched and no Git-link pins are changed.

## Website generation and manual publication

Generation is opt-in, not part of the default app build:

```sh
cmake --build build --target website
```

The adapter recreates only `build/website/doc/`, copies compiler documentation
Markdown into that staged `doc/` and website content/generator into its child
`website/`, then runs the pinned cwd-relative generator there. Each invocation
reads current inputs and removes stale output pages. It produces all compiler
Markdown pages, the site pages, docs-manifest index, CSS and JavaScript under
`build/website/doc/website/site/`. Missing manifest documents or assets are
errors, not silently skipped pages. Component sources remain untouched.

The pinned `cwhip-doxygen-link.zip` contains site sources/assets, **no Doxygen
HTML reference**. Without an explicit HTML input, generation emits a diagnostic
and removes the unavailable API reference from the staged docs index. It does
not invent an API page or run the compiler's source-tree-writing Doxygen rules.
To include an existing reviewed reference:

```sh
cmake -S . -B build -DCWHIP_WEBSITE_API_HTML=/absolute/path/to/doxygen/html
cmake --build build --target website
```

That directory must contain `index.html`; its complete contents are copied to
the generated `site/html/` and the manifest API link is retained. Fresh API
generation is future work. The pinned Markdown renderer is deliberately
simple; this adapter does not claim exhaustive cross-document/anchor validation.

**WEBSITE UPLOAD MANUAL.** Review the generated site locally, including its
docs, assets and any supplied API reference, before manually publishing.
Never run `website/install.sh` from this workflow: it uploads via SCP.
There is no upload/deploy target.

## Validation

The default seven CTest entries cover read-only component diagnostics, existing
status unit tests plus website tests, native PTY transport, compiler compilation
and execution through root `bin/cwhip`, root package-tool discovery,
launcher sibling resolution with a harmless test companion, `bin/cdbg --help`,
publication switching/repair/no-op behavior, exact embedded inspector bytes, real GDB value
inspection, unchanged second-build timestamps and the external debugger's MI
parser checks. GDB absence is explicitly reported as a skipped inspector check;
an installed GDB without the required Python API fails that check.
The inspector fixture links a debug-built runtime object so its private DWARF
types remain available even when the staged runtime is built without symbols.
The full compiler/GUI suites are not implied by these focused checks.

For an explicit dependency probe after a GUI-enabled default build:

```sh
python3 tests/build_checks.py --mode dependencies --build build
python3 scripts/status.py
git submodule status --recursive
git diff --check
git status --short
```

This opt-in probe temporarily touches app sources, launcher, MI/terminal
sources, inspector/embed scripts, a runtime header, a package manifest and
staged native/runtime archives, requires the relevant binary to rebuild,
restores input timestamps in `finally`, then checks a no-op build. It does not
edit component content; do not run it concurrently with another build in the
same directory. CTest itself does not touch component timestamps.
