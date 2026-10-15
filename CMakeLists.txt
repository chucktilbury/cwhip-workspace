cmake_minimum_required(VERSION 3.24)
project(cwhip_workspace LANGUAGES C CXX)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "Use an out-of-source build: cmake -S . -B build")
endif()
get_property(multi_config GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(multi_config)
    message(FATAL_ERROR "This bootstrap requires a single-config generator (Unix Makefiles or Ninja). Use a separate build directory per configuration.")
endif()
foreach(component compiler editor debugger website)
    file(REAL_PATH "${CMAKE_SOURCE_DIR}/${component}" component_source)
    file(REAL_PATH "${CMAKE_BINARY_DIR}" workspace_binary)
    cmake_path(IS_PREFIX component_source "${workspace_binary}" NORMALIZE inside_component)
    if(inside_component)
        message(FATAL_ERROR "The binary directory must not be inside the ${component} submodule")
    endif()
    if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${component}/.git")
        message(FATAL_ERROR
            "${component} is not initialized. Run git submodule update --init --recursive explicitly, then configure again.")
    endif()
endforeach()

find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(GTK4 QUIET "gtk4>=4.10")
    pkg_check_modules(SOURCEVIEW QUIET gtksourceview-5)
endif()
option(CWHIP_GTK "Build the compiler's GTK bindings" ${GTK4_FOUND})
set(sourceview_default OFF)
if(CWHIP_GTK AND SOURCEVIEW_FOUND)
    set(sourceview_default ON)
endif()
option(CWHIP_GTK_SOURCEVIEW "Build the compiler's GtkSourceView bindings" ${sourceview_default})
option(CWHIP_BUILD_CEDIT "Include the external editor in the default build" ON)
option(CWHIP_BUILD_CDBG "Include the external debugger in the default build" ON)

set(workspace_stage "${CMAKE_BINARY_DIR}/stage")
set(compiler_build "${CMAKE_BINARY_DIR}/compiler-build")
set(workspace_bin "${workspace_stage}/bin")
set(workspace_public_bin "${CMAKE_SOURCE_DIR}/bin")
set(workspace_enabled_bins cwhip cwhip-pkg)
if(CWHIP_GTK_SOURCEVIEW AND CWHIP_BUILD_CEDIT)
    list(APPEND workspace_enabled_bins cedit cedit.bin)
endif()
if(CWHIP_GTK_SOURCEVIEW AND CWHIP_BUILD_CDBG)
    list(APPEND workspace_enabled_bins cdbg)
endif()
set(workspace_publish "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/publish_bin.py"
    --stage "${workspace_stage}" --output "${workspace_public_bin}"
    --enabled ${workspace_enabled_bins})
set(workspace_modules "${workspace_stage}/share/cwhip/modules")
set(workspace_compiler "${workspace_bin}/cwhip")
set(runtime_archive "${workspace_stage}/lib/cwhip/libcwhip_runtime.a")
set(sqlite_archive "${workspace_modules}/sqlite/0.1.0/lib/libcwhip_sqlite.a")
set(gtk_archive "${workspace_modules}/gtk/0.1.0/lib/libcwhip_gtk.a")
set(resource_stamp "${compiler_build}/src/cwhip-resources.stamp")

# A separate top-level configure preserves the compiler's CMAKE_SOURCE_DIR
# assumptions without inheriting its integrated application or website targets.
file(GLOB_RECURSE compiler_cmake CONFIGURE_DEPENDS
    "${CMAKE_SOURCE_DIR}/compiler/CMakeLists.txt"
    "${CMAKE_SOURCE_DIR}/compiler/*.cmake"
    "${CMAKE_SOURCE_DIR}/compiler/*/CMakeLists.txt")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${compiler_cmake})
execute_process(
    COMMAND "${CMAKE_COMMAND}" -S "${CMAKE_SOURCE_DIR}/compiler" -B "${compiler_build}"
        -G "${CMAKE_GENERATOR}"
        "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
        "-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
        "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
        "-DCMAKE_MAKE_PROGRAM=${CMAKE_MAKE_PROGRAM}"
        "-DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
        "-DCWHIP_STAGE_PREFIX=${workspace_stage}"
        "-DCMAKE_INSTALL_PREFIX=${workspace_stage}"
        -DCMAKE_INSTALL_BINDIR=bin -DCMAKE_INSTALL_LIBDIR=lib
        -DCMAKE_INSTALL_INCLUDEDIR=include -DCMAKE_INSTALL_DATADIR=share
        "-DCWHIP_GTK=${CWHIP_GTK}" "-DCWHIP_GTK_SOURCEVIEW=${CWHIP_GTK_SOURCEVIEW}"
        -DBUILD_TESTING=OFF
    COMMAND_ERROR_IS_FATAL ANY)
load_cache("${compiler_build}" READ_WITH_PREFIX compiler_ CWHIP_CLANG_EXECUTABLE)
set(compiler_outputs "${workspace_compiler}" "${runtime_archive}" "${sqlite_archive}"
    "${resource_stamp}")
if(CWHIP_GTK)
    list(APPEND compiler_outputs "${gtk_archive}")
endif()
add_custom_target(cwhip ALL
    COMMAND "${CMAKE_COMMAND}" --build "${compiler_build}" --config "$<CONFIG>" --target cwhip
    COMMAND ${workspace_publish} --names cwhip cwhip-pkg
    BYPRODUCTS ${compiler_outputs}
    USES_TERMINAL VERBATIM)

set(workspace_environment "${CMAKE_COMMAND}" -E env
    --unset=CWHIP_PACKAGE_PATH --unset=CWHIP_MODULE_REGISTRY --unset=CWHIP_MODULE_DIR
    --unset=DESTDIR
    "CWHIP_HOME=${workspace_stage}"
    "CWHIP_RUNTIME_DIR=${workspace_stage}/lib/cwhip"
    "CWHIP_INCLUDE_DIR=${workspace_stage}/include"
    "CWHIP_BUILTIN_DIR=${workspace_stage}/share/cwhip/builtin"
    "CWHIP_STDLIB_MODULE_DIR=${workspace_modules}"
    "PYTHONDONTWRITEBYTECODE=1"
    "CC=${compiler_CWHIP_CLANG_EXECUTABLE}")

include(cmake/Applications.cmake)

set(CWHIP_WEBSITE_API_HTML "" CACHE PATH "Optional existing Doxygen HTML directory containing index.html")
add_custom_target(website
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/build_site.py"
        --compiler-doc "${CMAKE_SOURCE_DIR}/compiler/doc"
        --website "${CMAKE_SOURCE_DIR}/website"
        --work "${CMAKE_BINARY_DIR}/website"
        "--api-html=${CWHIP_WEBSITE_API_HTML}"
    USES_TERMINAL VERBATIM)

include(CTest)
if(BUILD_TESTING)
    include(cmake/Tests.cmake)
endif()
message(STATUS "Workspace executables: ${workspace_public_bin} (private stage: ${workspace_stage}); website is opt-in")
