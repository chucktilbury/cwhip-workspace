# Workspace CMake build

For a beginner walkthrough including prerequisites, a persistent user-local
installation, launching cedit, editing and running hello world, start with
[Your first program](FIRST-PROGRAM.md).

## Prerequisites and default build

Initialize the selected revisions explicitly before configuring:

```sh
git submodule update --init --recursive
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

The selected editor and debugger revisions must each contain their standalone
root `CMakeLists.txt`. Configuration fails immediately with the exact missing
path if either interface is absent, even in compiler-only configurations.
A workspace commit does not include uncommitted changes inside submodules.
The selected pins contain these interfaces and can be initialized normally;
no private patches or another worktree's files are required. An older pin
cannot acquire a new interface merely by reinitializing it: use the selected
workspace revisions, not copied uncommitted component files.
`test-all` also preflights both interfaces before
creating its private outputs or building compiler suites, protecting existing
build directories if a component checkout changes after configuration.

Requirements: Linux/POSIX, CMake >= 3.24, a C11/C++17 toolchain, Clang on
PATH, Python >= 3.11 (standard library only), SQLite 3 development files,
and the **Unix Makefiles** generator. Other generators, including Ninja, are
rejected at configure time because recursive standard clean needs the
Makefiles per-language clean-script include. No package downloads or system installs
are performed. Use `-DCMAKE_BUILD_TYPE=Debug` for compiler/runtime debug
symbols, or `Release` for optimization. The compiler's normal default is
preserved when no build type is selected. GNU/Clang SDK runtimes retain type
debug metadata even in Release, for source-free debugger object inspection;
this does not change runtime optimization or bundle system libraries.

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
uses the user's desktop, deploys a website, or requires hosting credentials.
The focused root CTest invokes `cdbg --help` only, without creating a window;
`test-all` also runs automated GUI checks on isolated Xvfb/DBus sessions.
Manual GUI launch and
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

## Outputs and installed SDK boundary

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
published. Standard clean removes only links owned by the cleaned build,
leaving another configuration's links untouched. Manually deleting an active
binary directory without cleaning can leave dangling links; build again to
restore them. Root links are ownership-aware, not unconditional clean byproducts.
The links themselves are not a distribution. Their target `stage/` is now an
installed SDK/application prefix; move/copy that entire prefix, not root links.

Intermediates, real executable files, copied resources and generated package
locks remain in the selected binary directory, here shown as `build/`:

| Path | Contents |
| --- | --- |
| `compiler-build/` | Separate compiler CMake configuration and object files |
| `compiler-stage/` | Compiler build outputs/resources, separate from installation |
| `stage/bin/` | `cwhip`, generated `cwhip-pkg`, `cedit` launcher, `cedit.bin`, `cdbg` |
| `stage/lib/cwhip/` | Runtime archive |
| `stage/include/cwhip/` | Installed public runtime headers |
| `stage/lib/cmake/Cwhip/` | Exact-version installed CMake SDK contract |
| `stage/share/cwhip/builtin/` | Builtin language sources |
| `stage/share/cwhip/modules/` | Standard packages, SQLite/GTK native archives, SourceView language resources |
| `apps/cedit/`, `apps/cdbg/` | Independent app CMake build trees, native objects, private source projects/locks/HOME/XDG; debugger `values.h` |
| `tests/` | Focused test binaries, fixtures and isolated configuration |
| `website/doc/website/site/` | Explicitly generated site |
| `test-all/` | Full compiler Debug build/stage/install, independent app builds and isolated test outputs |

Application builds use the installed compiler's package discovery and
`cwhip-pkg init` to lock the standard packages. Runtime/include/builtin/module
paths are set to the selected installed prefix, legacy and user module overrides are
cleared, and HOME/XDG configuration is isolated per app. No user package
configuration is imported. Changes to native archives, SDK headers/resources,
package manifests, app sources, launcher, terminal helper and inspector/embed
scripts participate in incremental dependencies. Source copies are refreshed
when rebuilding an app, so removed files cannot linger in its staged sources.

The compiler is built into `compiler-stage/`, then its native CMake install
rules populate `stage/`. Each application is configured from its own project
root with `CMAKE_PREFIX_PATH=stage`; the umbrella no longer compiles app sources
or borrows compiler-owned app fixtures. Both applications own build, test,
clean and install interfaces. Their installation merges executable files and
resources into the same private prefix. Installed apps/resources contain no
required compiler/workspace source path; GTK discovers bundled language
definitions relative to the running executable.

The supported boundary is a **whole-prefix, exact-version prototype SDK**,
not literal executable-only portability or production release packaging.
The bundle needs runtime archive, public headers, builtins, standard packages
and native archives as well as cwhip/cwhip-pkg. External Clang, Python, Git
(for explicit package installation), native platform/GUI development and
runtime libraries remain prerequisites. See the compiler's
[SDK contract](../compiler/doc/CMAKE-SDK.md), editor's
[standalone build](../editor/doc/BUILD.md) and debugger's
[standalone build](../debugger/doc/BUILD.md). For example:

```sh
cp -a build/stage /chosen/relocated-sdk
cmake -S editor -B /chosen/editor-build \
  -DCMAKE_PREFIX_PATH=/chosen/relocated-sdk
cmake --build /chosen/editor-build --target test-all
cmake --install /chosen/editor-build --prefix /chosen/editor-install
```

Replace `editor` with `debugger` for cdbg. These projects can be copied or
cloned outside the umbrella without compiler checkout paths. Install the
compiler independently using its documented `CWHIP_STAGE_PREFIX` and separate
`CMAKE_INSTALL_PREFIX` if no umbrella is wanted.
App options changed in an existing workspace directory can leave old private
installed files, but disabled named targets still fail and root links are
not published. Use a new binary directory for a pristine output set.

The compiler's integrated apps, website and shell install scripts are not
built/run by the default workspace orchestration. No Git-link pins change.
Component implementation changes remain owned by their respective repositories.

## Clean

```sh
cmake --build build --target clean
cmake --build build
# Or clean and rebuild in one invocation:
cmake --build build --clean-first --parallel 4
```

This is CMake's **standard clean target**, not a replacement named target.
It propagates to the compiler and configured app native clean targets,
removing their objects and artifacts. It then removes this binary directory's
compiler build stage, entire installed private stage,
app build trees, generated source copies/native headers/package locks/HOME/config,
test outputs and logs, full `test-all/` trees, and generated website staging.
Root native objects/executables are removed by CMake's own native clean rules.
The source tree, pins, other binary directories and their published links
are preserved. Repeated clean is harmless.

Root and nested compiler caches/Makefiles and dependency metadata are
retained. An ordinary subsequent build reruns the compiler configure/build/
install, then recreates independent app configurations before building and
installing them. No manual configure step is required after clean. Standalone
app clean preserves its own configure state and input inventories for direct
rebuild without reconfiguration.
The website remains opt-in and must be regenerated explicitly.

The propagation hook is configured from `cmake/CleanHook.cmake.in` into a
dedicated non-default object's optional `cmake_clean_C.cmake` include, which
the Unix Makefiles generator emits after its native target cleanup. It does
not patch CMake's main generated clean scripts. This narrow generator-specific
extension is why other generators are rejected rather than given incomplete
clean semantics. Nested clean failures are fatal. Do not run clean concurrently
with a build/test in that same directory, nor run different configurations'
builds/tests concurrently while sharing root `bin/`.

The explicit destructive-to-products regression exercises populated builds,
website and tests, repeat clean, rebuild, clean-first and inactive ownership:

```sh
python3 tests/clean_checks.py --build build --active-build "build gui spaces"
```

Both arguments must already be configured; the second is optional and must
refer to a different build directory. It finishes with the second build
active and the first cleaned. These regressions are opt-in so ordinary CTest
does not delete its own working products.

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

### All supported suites

```sh
cmake -S . -B build
cmake --build build --target test-all
```

`test-all` requires `BUILD_TESTING=ON`. It first builds the selected workspace
compiler/apps and native test, then configures a separate **Debug** compiler
test build/stage under `build/test-all/`. It builds compiler unit/functional,
command-line and GC test executables and runs the compiler's registered CTest
suite with `--output-on-failure`. This includes integration cases, callbacks,
package CLI (remote operations mapped to local test repositories), developer
setup, install-layout regressions in temporary private prefixes, examples,
documentation programs and enabled GTK binding checks. It does not invoke
`install.sh`, deploy, or install into system/user directories.

The compiler CTest excludes `cedit_*`, `cdbg_*` and
`cwhip_example_editor_*`: those exercise compiler-monorepo app duplicates,
not the extracted apps. The target prints that exclusion and instead runs
the standalone editor's actual binary/default-shortcut smoke, shortcuts,
four preference groups, four project groups and editor-owned
project-explorer/dialog fixtures. It runs the standalone debugger's native
terminal/embedded script, MI parser and local-GDB session tests. App CMake
projects consume the installed Debug SDK, not compiler test sources or
an umbrella fixture adapter. The umbrella additionally passes
`CDBG_RUNTIME_SOURCE` to cover compiler-private source-line stepping in the
matching Debug runtime and labels that source-specific integration explicitly.
Source-free standalone suites do not require that file; they visibly exclude
only the private-runtime source-line check, while other applicable
inspection/session regressions still run.
Workspace CTests run as well, including status, publication, clean-helper
unit tests and website Markdown/assets/manifest tests; the pinned website
has no separate test runner.
The relocated SDK external hello/stdlib/inline-C/native binding, clean/install
and invalid-prefix/version acceptance also runs. Repeating full app suites
after independent copying/installation/relocation is the separate opt-in
`check-sdk` regression, like destructive `clean_checks.py` and `check-noop`.

GTK test programs use ephemeral isolated Xvfb displays and DBus sessions,
not the user's display. Missing optional Xvfb/DBus, disabled apps/bindings,
or missing GDB produce visible suite exclusions; compiler/non-GUI and root
focused tests still run. An installed but incompatible tool fails the
relevant test. Fuzz/sanitizer/coverage instrumentation is not enabled by this
target and is explicitly distinguished from the normal registered suites.
HOME/XDG, temporary prefixes and test outputs are private to the binary tree.

Compiler and external CTest invocations run serially (`--parallel 1`) to
avoid fixture/display/build-resource conflicts; compiler test executable
compilation uses bounded `--parallel 4`. The driver drops inherited Make
jobserver flags before its own bounded builds, avoiding invalid jobserver
descriptors. Suite failures are retained while remaining suites run, and
`test-all` fails if any suite fails; it does not silently turn failures into
success or download missing tools.

### Focused checks

If `workspace_diagnostics` reports `MISMATCH`, see
[Troubleshooting: pin MISMATCH](WORKFLOW.md#troubleshooting-pin-mismatch)
for recording intended component revisions or restoring the committed pins.

The default six CTest entries cover read-only component diagnostics, existing
status unit tests plus website tests, native PTY transport, compiler compilation
and execution through root `bin/cwhip`, root package-tool discovery,
launcher sibling resolution with a harmless test companion, `bin/cdbg --help`,
publication switching/repair/no-op behavior, exact embedded inspector bytes, real GDB value
inspection and the external debugger's MI
parser checks. GDB absence is explicitly reported as a skipped inspector check;
an installed GDB without the required Python API fails that check.
Diagnostics report local component edits but only uninitialized/mismatched
pins fail the CTest (`status.py --allow-dirty`); plain `status.py` remains
strict. This permits deliberate coordinated development without disguising
dirty components as clean.
The inspector fixture links a debug-built runtime object so its private DWARF
types remain available even when the staged runtime is built without symbols.
The full compiler/GUI suites are not implied by these focused checks.

For an explicit dependency probe after a GUI-enabled default build:

```sh
cmake --build build --target check-noop
cmake --build build --target check-sdk
python3 tests/build_checks.py --mode dependencies --build build
python3 scripts/status.py
git submodule status --recursive
git diff --check
git status --short
```

Ordinary `make test` / CTest reuses built artifacts: it does not invoke the
workspace's default build again. The explicit `check-noop` target retains
the incremental-build regression: it snapshots compiler/app/resource and
publication timestamps, invokes a default build, and fails if anything is
rewritten. Run it after building the desired configuration; do not run it
concurrently with another build in that directory. It is intentionally outside
default CTest and `test-all`, since it re-enters the main build. Compilation
smoke tests still compile small test programs, not the compiler itself.

This opt-in probe temporarily touches app sources, launcher, MI/terminal
sources, inspector/embed scripts, a runtime header, a package manifest and
compiler build-stage native/runtime archives, requires the relevant binary to rebuild,
restores input timestamps in `finally`, then checks a no-op build. It does not
edit component content; do not run it concurrently with another build in the
same directory. CTest itself does not touch component timestamps.

`check-sdk` explicitly exercises the installed contract: copy and rename the
whole prefix into a temporary external path containing spaces, compile/run the
tracked `examples/hello-world` through both CLI and CMake, edit its greeting
and verify both rebuilds, then compile/run an external CMake program using
standard modules, inline C and a public-header
native object, reject missing runtime and wrong version, and test clean/
rebuild/install. With both apps enabled it copies each standalone project
outside the umbrella, configures it only against that relocated SDK, runs its
full suite/no-op check, installs/relocates/launches it headlessly or with
`--help`, and cleans/rebuilds/tests it again. HOME/XDG are empty/private and no
CWHIP source overrides are inherited. Installed config scripts/path discovery
are checked for workspace/build-stage leakage. Debug DWARF can name original
source files but is not a runtime resource fallback. The test removes its
ephemeral external tree/displays/session buses on completion.
It explicitly uses a private `/tmp` child rather than inherited `TMPDIR`, so
even invocation from `test-all` stays outside the umbrella source/binary tree.
The check visibly excludes app relocation when both GUI apps are not enabled.
