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

## Workflow index

- [Recursive clone and initialization; updating to pinned revisions](doc/WORKFLOW.md#clone-and-restore-pinned-revisions)
- [Deliberate updates, branches, detached HEAD, and two-level commits](doc/WORKFLOW.md#develop-and-update-components-deliberately)
- [Setup and dependency plan; incomplete standalone builds and website setup](doc/WORKFLOW.md#dependency-and-setup-plan)
- [Validation commands](doc/WORKFLOW.md#workspace-validation)
- [Unresolved licensing](doc/WORKFLOW.md#licensing)

## Planning index

The [Cwhip Applications project](https://github.com/users/chucktilbury/projects/1)
tracks deferred work across the components. File workspace coordination issues
in [this repository](https://github.com/chucktilbury/cwhip-workspace/issues);
file component changes with the owning repository. Existing component issues
are linked in the [workflow plan](doc/WORKFLOW.md#dependency-and-setup-plan).
