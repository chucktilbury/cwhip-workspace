# Cwhip workspace

Pinned development umbrella for the Cwhip compiler, editor, debugger, and
website. Component source and history remain owned by their repositories;
this repository owns the selected revisions and cross-repository workflow.

## Directory index

| Path | Owner / contents |
| --- | --- |
| [`compiler/`](https://github.com/chucktilbury/cwhip) | `cwhip`: compiler, runtime, standard library, shared bindings, compiler documentation |
| [`editor/`](https://github.com/chucktilbury/cedit) | `cedit`: editor source and application documentation |
| [`debugger/`](https://github.com/chucktilbury/cdbg) | `cdbg`: debugger source and application documentation |
| [`website/`](https://github.com/chucktilbury/cwhip-website) | `cwhip-website`: site sources, generator, and publication assets |
| [`doc/WORKFLOW.md`](doc/WORKFLOW.md) | Setup, dependency stages, development, validation, and manual publication plan |
| [`scripts/status.py`](scripts/status.py) | Read-only pinned/current component diagnostics |
| [`tests/test_status.py`](tests/test_status.py) | Isolated status-script tests |
| [`CMakeLists.txt`](CMakeLists.txt) | Isolated compiler bootstrap, external apps, opt-in website and CTest |
| [`doc/BUILD.md`](doc/BUILD.md) | Build options, output layout, focused checks and current SDK limitations |

## Build

After initializing the pinned submodules:

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

The compiler builds first; GTK-enabled builds also produce the **external**
editor and debugger. Executables are in `build/stage/bin/`. Compiler-only
builds, prerequisites and custom paths are described in [doc/BUILD.md](doc/BUILD.md).
Website generation is explicit: `cmake --build build --target website`.
Its output is `build/website/doc/website/site/`. **WEBSITE UPLOAD MANUAL**:
no build or test deploys anything, and `website/install.sh` must not be run.

## Workflow index

- [Recursive clone and initialization; updating to pinned revisions](doc/WORKFLOW.md#clone-and-restore-pinned-revisions)
- [Deliberate updates, branches, detached HEAD, and two-level commits](doc/WORKFLOW.md#develop-and-update-components-deliberately)
- [Workspace build commands and options](doc/BUILD.md)
- [Dependency stages and remaining standalone SDK work](doc/WORKFLOW.md#dependency-and-setup-plan)
- [Validation commands](doc/WORKFLOW.md#workspace-validation)
- [Unresolved licensing](doc/WORKFLOW.md#licensing)

## Planning index

The [Cwhip Applications project](https://github.com/users/chucktilbury/projects/1)
tracks deferred work across the components. File workspace coordination issues
in [this repository](https://github.com/chucktilbury/cwhip-workspace/issues);
file component changes with the owning repository. Existing component issues
are linked in the [workflow plan](doc/WORKFLOW.md#dependency-and-setup-plan).
