# From no Cwhip installation to a first program

This guide describes the intended 0.0.2 `numeric-v2` source-install path on
Linux/POSIX. It builds the compiler SDK and standalone `cedit`, installs into
your own directory, then edits, builds and runs a small program outside the
checkout. It does not require another developer's build tree, private files, a
website, or a packaged Cwhip release. Cwhip and cedit are prototypes.

**This guide cannot be followed from the currently committed workspace pins.**
They still select 0.0.1 compiler and consumer revisions, while this guide's
example requires Cwhip 0.0.2 with ABI `numeric-v2`. The compiler and consumer
migrations listed in [WORKFLOW.md](WORKFLOW.md#numeric-v2-integration) have
merged upstream but have not been selected by this workspace. Wait for
compatible pins before using the clone/build steps below. The numeric-v2 SDK
is source- and native-ABI-incompatible with 0.0.1; rebuild native packages and
do not mix files from different SDK prefixes.

Already have a complete installed SDK and cedit? Set `CWHIP_PREFIX` and `PATH`
as in step 3, then create `hello.cw` yourself using step 4's File > New
instructions rather than copying the checkout example. Writing a program
does not require a workspace clone, submodules, or contributor/PR workflows.

Run the commands in order in one terminal (a POSIX shell such as bash). Paths
are quoted so a home directory containing spaces works. No command below
installs Cwhip system-wide.

## 1. Check system prerequisites

You need Git, GNU Make, CMake **3.24+**, Python **3.11+**, a C11/C++17 native
toolchain, Clang, SQLite 3 development files, pkg-config, GTK **4.10+** and
GtkSourceView **5** development files. A graphical desktop/display is required
to use cedit interactively.

On a sufficiently recent Debian/Ubuntu system, the relevant distribution
package names are:

```text
git build-essential cmake clang python3 pkg-config libsqlite3-dev
libgtk-4-dev libgtksourceview-5-dev
```

Have your system administrator install missing prerequisites using the
distribution's package manager; the Cwhip build does not install them.
Package names alone do not guarantee sufficiently new versions: for example,
Debian 12's GTK 4.8 is too old for cedit. Check before building:

```sh
git --version
make --version
cmake --version
python3 --version
cc --version
c++ --version
clang --version
pkg-config --modversion sqlite3 gtk4 gtksourceview-5
pkg-config --atleast-version=4.10 gtk4
```

The last command must exit successfully. CMake also checks the required
dependencies. GDB is **not** needed for this tutorial; we leave the debugger
disabled. Xvfb and dbus-daemon are optional for automated headless editor
checks, not prerequisites for interactive use.

## 2. Clone and build the selected sources

Choose a new source directory; the following assumes `~/Src/cwhip-workspace`
does not already exist:

```sh
mkdir -p "$HOME/Src"
git clone --recurse-submodules \
  https://github.com/chucktilbury/cwhip-workspace.git \
  "$HOME/Src/cwhip-workspace"
cd "$HOME/Src/cwhip-workspace"
export CWHIP_WORKSPACE="$PWD"
git submodule status --recursive

cmake -S "$CWHIP_WORKSPACE" -B "$CWHIP_WORKSPACE/build-first" \
  -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release \
  -DCWHIP_GTK=ON -DCWHIP_GTK_SOURCEVIEW=ON -DCWHIP_BUILD_CDBG=OFF
cmake --build "$CWHIP_WORKSPACE/build-first" --parallel 4
```

All submodule status lines should start with a space, not `-`, `+` or `U`.
An existing clean clone can restore its pins with
`git submodule update --init --recursive`; preserve any component edits first.
Do not use `--remote`: the workspace selects compatible committed revisions.

The explicit GUI options are intentional: if dependencies are missing,
configuration must fail rather than silently build only the compiler.
The workspace builds/installs the SDK first and then builds cedit through
its own standalone CMake project against that installed SDK. Do not use
the compiler repository's legacy integrated editor build instructions.
The website is not built or uploaded.

## 3. Install a complete user-local prefix

Use a dedicated directory, not `/usr` or `/usr/local`. The workspace's private
`stage/` is already an installed tree, but its lifetime is tied to the build.
Install a persistent copy through the **component** install interfaces:

```sh
export CWHIP_PREFIX="$HOME/.local/opt/cwhip-0.0.2"
cmake --install "$CWHIP_WORKSPACE/build-first/compiler-build" \
  --prefix "$CWHIP_PREFIX"
cmake --install "$CWHIP_WORKSPACE/build-first/apps/cedit" \
  --prefix "$CWHIP_PREFIX"

export PATH="$CWHIP_PREFIX/bin:$PATH"
unset CWHIP_HOME CWHIP_RUNTIME_DIR CWHIP_INCLUDE_DIR CWHIP_BUILTIN_DIR
unset CWHIP_STDLIB_MODULE_DIR CWHIP_MODULE_DIR CC
command -v cwhip
command -v cedit
cwhip --print-paths
```

Choose a new prefix if that directory contains another installation you want
to keep; installation updates files in the destination. No `sudo` is needed.
There is no workspace-root `cmake --install` interface: the two commands above
install the compiler SDK and editor with their resources into the same prefix.
`--print-paths` should resolve the executable, runtime, headers, builtins and
standard packages under `CWHIP_PREFIX`, not a checkout or old installation.
Clang and system development libraries remain external prerequisites.

Keep the **whole prefix**, including `lib/`, `include/` and `share/`, not just
`bin/cwhip` or the workspace's `bin/` symlinks. You may move the complete prefix
and update `CWHIP_PREFIX`/`PATH`; there is no source-checkout dependency for use.
Cleaning the workspace does not remove this separate installation.
Do not run the component shell install scripts.

These exports affect only the current shell. In a new terminal, set
`CWHIP_PREFIX` and `PATH` again before following the remaining steps; if older
Cwhip overrides exist, unset them as above. Nothing edits your shell startup
files.

## 4. Create and edit hello world

Choose a new project directory outside the source checkout. Copy the small
tracked example (no package downloads or project generator required):

```sh
mkdir -p "$HOME/Src/cwhip-hello"
cd "$HOME/Src/cwhip-hello"
cp "$CWHIP_WORKSPACE/examples/hello-world/hello.cw" .
cp "$CWHIP_WORKSPACE/examples/hello-world/CMakeLists.txt" .
cedit hello.cw
```

Use an empty directory so `cp` does not replace existing work. The file contains:

```cwhip
start {
    print("Hello, world!\n")
}
```

The launcher presents the editor and returns the terminal prompt. Change
`Hello, world!` to `Hello from Cwhip!`, then press **Ctrl+S** (File > Save).
The tab's `*` modified marker should disappear. To create the file yourself,
use **File > New**, type the source above, and **File > Save As...** to save
`hello.cw` in this directory; the `.cw` suffix enables syntax highlighting.
**Ctrl+O** opens an existing file; **Ctrl+Q** quits with unsaved-change protection.

You do **not** need Project > New Project for this program. Editor project
metadata (`.cwhip/project.toml`) saves editor/workspace settings; it is not a
compiler manifest or CMake build configuration. The pinned editor has no
integrated build/run command. Use the terminal for the next step.

## 5. Build, run, edit and rebuild

From the same `cwhip-hello` directory:

```sh
cwhip hello.cw -o hello
./hello
```

After the edit above the output is:

```text
Hello from Cwhip!
```

Before editing it is `Hello, world!`. Change the string again, save in cedit,
and repeat **both** terminal commands. Running `./hello` without recompiling
runs the old executable. A failed compilation must be corrected before running;
do not mistake an existing old executable for a successful new build.
This program uses only builtins, so `cwhip-pkg init` is unnecessary.

### Optional: build the same program with the installed CMake SDK

The copied `CMakeLists.txt` contains:

```cmake
cmake_minimum_required(VERSION 3.24)
project(hello_world LANGUAGES C)
find_package(Cwhip 0.0.2 EXACT CONFIG REQUIRED)
cwhip_add_program(hello SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/hello.cw")
```

Select the **whole installed prefix**, not its `bin/` directory:

```sh
cmake -S . -B build -G "Unix Makefiles" \
  -DCMAKE_PREFIX_PATH="$CWHIP_PREFIX"
cmake --build build --parallel 4
./build/bin/hello
```

After editing and saving `hello.cw`, repeat the build and run commands.
The SDK helper tracks source changes. Its output is `build/bin/hello`, distinct
from the earlier CLI-built `./hello`. The exact SDK version is intentional;
the prototype does not promise compatibility across compiler/runtime versions.
Use a new build directory when changing SDK installations.

## If something goes wrong

| Symptom | Action |
| --- | --- |
| Missing submodule / standalone CMake project | Restore the workspace's committed submodules; do not borrow another session's uncommitted files. |
| GTK/SourceView configure failure | Check development packages and minimum GTK version. Reconfigure with both GUI options ON after fixing dependencies. |
| `cwhip` or `cedit` not found | Set `CWHIP_PREFIX` and export its `bin/` on PATH in this terminal. |
| Compiler resource paths point at another installation | Clear resource overrides as above; inspect `command -v cwhip` and `cwhip --print-paths`. User/project package roots may legitimately be outside the prefix. |
| Editor cannot open a display | Launch from a working graphical session. An SSH/headless shell alone does not provide a desktop. |
| Output did not change | Save the correct `.cw` file, check compilation succeeded, then run the matching CLI or CMake executable. |
| CMake cannot find Cwhip 0.0.2 | Pass the installed prefix, check it includes `lib/cmake/Cwhip`, and use a fresh build directory. |

Without sufficiently new GTK/SourceView, the compiler-only path still works:
use a **separate** build directory with `-DCWHIP_GTK=OFF
-DCWHIP_GTK_SOURCEVIEW=OFF -DCWHIP_BUILD_CEDIT=OFF -DCWHIP_BUILD_CDBG=OFF`,
install only its `compiler-build`, and edit with your existing text editor.
That is not a cedit installation.

## Source installation now; Debian packaging later

This guide does not claim a Cwhip `.deb`, apt repository, desktop entry or
binary release exists. System package names above are prerequisites, not
Cwhip packages. Future Debian packages must follow Debian Policy, use
standard install directories (including multiarch where appropriate),
support staged `DESTDIR` installation, declare build/runtime dependencies,
and supply verified copyright/license and maintainer metadata.
Those identities and redistribution permissions remain owner decisions;
do not infer them from public repository visibility.

The dedicated user-local prefix here avoids system-managed files. It is not
a substitute for Debian packaging or a recommendation to install an
unreviewed prototype into `/usr`. See [the SDK boundary](BUILD.md#outputs-and-installed-sdk-boundary)
and [licensing status](WORKFLOW.md#licensing).
