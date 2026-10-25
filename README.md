# Cwhip workspace

Pinned development umbrella for the Cwhip compiler, cmacros CLI, editor,
debugger, and website. Component source and history remain owned by their repositories;
this repository owns the selected revisions and cross-repository workflow.

The workspace-owned `.cw` example and test-generated source use the current
Cwhip syntax. The compiler repository owns the language specification: see its
[grammar](https://github.com/chucktilbury/cwhip/blob/master/doc/GRAMMAR.md) and
[language reference](https://github.com/chucktilbury/cwhip/blob/master/doc/LANGUAGE-REFERENCE.md).

**New to Cwhip?** [From no installation to a first program](doc/FIRST-PROGRAM.md)
documents the intended 0.0.2 `numeric-v2` source-install workflow. It is not
usable with the currently committed 0.0.1 component pins; see the
[integration status](doc/WORKFLOW.md#numeric-v2-integration). This is not a
promise of available Debian binary packages.

## Directory index

| Path | Owner / contents |
| --- | --- |
| [`compiler/`](https://github.com/chucktilbury/cwhip) | `cwhip`: compiler, runtime, standard library, shared bindings, compiler documentation |
| [`cmacros/`](https://github.com/chucktilbury/cmacros) | `cmacros`: standalone Cwhip CLI macro processor and its examples/tests |
| [`editor/`](https://github.com/chucktilbury/cedit) | `cedit`: editor source and application documentation |
| [`debugger/`](https://github.com/chucktilbury/cdbg) | `cdbg`: debugger source and application documentation |
| [`website/`](https://github.com/chucktilbury/cwhip-website) | `cwhip-website`: site sources, generator, and publication assets |
| [`doc/WORKFLOW.md`](doc/WORKFLOW.md) | Setup, dependency stages, development, validation, and manual publication plan |
| [`scripts/status.py`](scripts/status.py) | Read-only pinned/current component diagnostics |
| [`tests/test_status.py`](tests/test_status.py) | Isolated status-script tests |
| [`CMakeLists.txt`](CMakeLists.txt) | Compiler SDK build/install, standalone apps, opt-in website and CTest |
| [`doc/BUILD.md`](doc/BUILD.md) | Build options, installed SDK boundary, checks and current limitations |
| [`examples/hello-world/`](examples/hello-world/) | Minimal first program and installed-SDK CMake project |

## Build

After initializing the pinned submodules:

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
cmake --build build --target test-all
```

The compiler SDK builds/installs first; the standalone `cmacros` CLI and
GTK-enabled editor/debugger are configured through their own CMake projects
against that installed prefix. `cmacros` does not require GTK. Executables are
available in workspace-root `bin/` through maintained links to the active
build's private stage. Headless builds, prerequisites and custom paths are
described in [doc/BUILD.md](doc/BUILD.md).
Website generation is explicit: `cmake --build build --target website`.
Its output is `build/website/doc/website/site/`. **WEBSITE UPLOAD MANUAL**:
no build or test deploys anything, and `website/install.sh` must not be run.
Use `cmake --build build --target clean` to clean all component products for
that build, or `cmake --build build --clean-first` to clean and rebuild.
The workspace currently requires the Unix Makefiles generator.
The complete `build/stage` prefix is relocatable; root links alone are not a
distribution. External projects consume the
[installed compiler SDK](compiler/doc/CMAKE-SDK.md), not a compiler checkout.
Run `cmake --build build --target check-sdk` for independent relocation and
application build/test/clean/install acceptance.

## Workflow index

- [Recursive clone and initialization; updating to pinned revisions](doc/WORKFLOW.md#clone-and-restore-pinned-revisions)
- [Deliberate updates, branches, detached HEAD, and two-level commits](doc/WORKFLOW.md#develop-and-update-components-deliberately)
- [Workspace build commands and options](doc/BUILD.md)
- [Dependency ownership and remaining release work](doc/WORKFLOW.md#dependency-and-setup-plan)
- [Validation commands](doc/WORKFLOW.md#workspace-validation)
- [Unresolved licensing](doc/WORKFLOW.md#licensing)

## Planning index

The [Cwhip Applications project](https://github.com/users/chucktilbury/projects/1)
tracks deferred work across the components. File workspace coordination issues
in [this repository](https://github.com/chucktilbury/cwhip-workspace/issues);
file component changes with the owning repository. Existing component issues
are linked in the [workflow plan](doc/WORKFLOW.md#dependency-and-setup-plan).
