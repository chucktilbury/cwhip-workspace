cmake_minimum_required(VERSION 3.24)
if(NOT CMAKE_GENERATOR STREQUAL "Unix Makefiles")
    message(FATAL_ERROR "This bootstrap requires Unix Makefiles for recursive standard clean support. Use -G \"Unix Makefiles\" and a separate build directory per configuration.")
endif()
project(cwhip_workspace LANGUAGES C CXX)
set(workspace_jobserver)
if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.28)
    set(workspace_jobserver JOB_SERVER_AWARE TRUE)
endif()

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "Use an out-of-source build: cmake -S . -B build")
endif()
foreach(component compiler editor debugger cmacros website)
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

foreach(component editor debugger cmacros)
    set(component_project "${CMAKE_CURRENT_SOURCE_DIR}/${component}/CMakeLists.txt")
    if(NOT EXISTS "${component_project}")
        message(FATAL_ERROR
            "Missing standalone ${component} project: ${component_project}\n"
            "This workspace requires the standalone component CMake interfaces. "
            "The checked-out component revision is too old or incomplete. "
            "Uncommitted additions in another component worktree are not included by workspace commits or submodule pins.\n"
            "Use the isolated checkout containing those component changes, or wait for the standalone component revisions "
            "to be committed/tagged and the workspace submodule pins updated, then initialize those selected revisions explicitly. "
            "Do not copy uncommitted component files implicitly.\n"
            "The later application configure would use: cmake -S \"${CMAKE_CURRENT_SOURCE_DIR}/${component}\" "
            "-B <application-build-directory>")
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
option(CWHIP_BUILD_CMACROS "Include the standalone cmacros CLI in the default build" ON)

set(workspace_stage "${CMAKE_BINARY_DIR}/stage")
set(compiler_stage "${CMAKE_BINARY_DIR}/compiler-stage")
set(compiler_build "${CMAKE_BINARY_DIR}/compiler-build")
set(workspace_bin "${workspace_stage}/bin")
set(workspace_public_bin "${CMAKE_SOURCE_DIR}/bin")
set(workspace_enabled_bins cwhip cwhip-pkg)
if(CWHIP_BUILD_CMACROS)
    list(APPEND workspace_enabled_bins cmacros)
endif()
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
set(compiler_configure "${CMAKE_COMMAND}" -S "${CMAKE_SOURCE_DIR}/compiler" -B "${compiler_build}"
        -G "${CMAKE_GENERATOR}"
        "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
        "-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
        "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
        "-DCMAKE_MAKE_PROGRAM=${CMAKE_MAKE_PROGRAM}"
        "-DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
        "-DCWHIP_STAGE_PREFIX=${compiler_stage}"
        "-DCMAKE_INSTALL_PREFIX=${workspace_stage}"
        -DCMAKE_INSTALL_BINDIR=bin -DCMAKE_INSTALL_LIBDIR=lib
        -DCMAKE_INSTALL_INCLUDEDIR=include -DCMAKE_INSTALL_DATADIR=share
        "-DCWHIP_GTK=${CWHIP_GTK}" "-DCWHIP_GTK_SOURCEVIEW=${CWHIP_GTK_SOURCEVIEW}"
        -DCWHIP_REGISTER_SDK=OFF
        -DBUILD_TESTING=OFF)
execute_process(COMMAND ${compiler_configure} COMMAND_ERROR_IS_FATAL ANY)
load_cache("${compiler_build}" READ_WITH_PREFIX compiler_ CWHIP_CLANG_EXECUTABLE)
set(compiler_outputs "${workspace_compiler}" "${runtime_archive}" "${sqlite_archive}"
    "${resource_stamp}")
if(CWHIP_GTK)
    list(APPEND compiler_outputs "${gtk_archive}")
endif()
add_custom_target(cwhip ALL
    COMMAND ${compiler_configure}
    COMMAND "${CMAKE_COMMAND}" --build "${compiler_build}" --config "$<CONFIG>" --target cwhip
    COMMAND "${CMAKE_COMMAND}" -E env --unset=DESTDIR
        "${CMAKE_COMMAND}" --install "${compiler_build}" --config "$<CONFIG>"
    COMMAND ${workspace_publish} --names cwhip cwhip-pkg
    BYPRODUCTS ${compiler_outputs}
    ${workspace_jobserver} USES_TERMINAL VERBATIM)

include(CTest)
include(cmake/Applications.cmake)
set(sdk_check_dependencies cwhip)
set(sdk_check_apps OFF)
if(CWHIP_GTK_SOURCEVIEW AND CWHIP_BUILD_CEDIT AND CWHIP_BUILD_CDBG)
    list(APPEND sdk_check_dependencies cedit cdbg)
    set(sdk_check_apps ON)
endif()
add_custom_target(check-sdk
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/sdk_checks.py"
        --prefix "${workspace_stage}" --cmake "${CMAKE_COMMAND}"
        --ctest "${CMAKE_CTEST_COMMAND}" "--apps=${sdk_check_apps}"
        "--cmacros=${CWHIP_BUILD_CMACROS}"
    DEPENDS ${sdk_check_dependencies} USES_TERMINAL VERBATIM)

set(CWHIP_WEBSITE_API_HTML "" CACHE PATH "Optional existing Doxygen HTML directory containing index.html")
add_custom_target(website
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/build_site.py"
        --workspace "${CMAKE_SOURCE_DIR}"
        --work "${CMAKE_BINARY_DIR}/website"
        "--api-html=${CWHIP_WEBSITE_API_HTML}"
    USES_TERMINAL VERBATIM)

if(BUILD_TESTING)
    include(cmake/Tests.cmake)
    set(test_all_dependencies cwhip workspace_terminal_test)
    if(CWHIP_BUILD_CMACROS)
        list(APPEND test_all_dependencies cmacros)
    endif()
    if(CWHIP_GTK_SOURCEVIEW AND CWHIP_BUILD_CEDIT)
        list(APPEND test_all_dependencies cedit)
    endif()
    if(CWHIP_GTK_SOURCEVIEW AND CWHIP_BUILD_CDBG)
        list(APPEND test_all_dependencies cdbg)
    endif()
    add_custom_target(test-all
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/test_all.py"
            --source "${CMAKE_SOURCE_DIR}" --build "${CMAKE_BINARY_DIR}"
            --cmake "${CMAKE_COMMAND}" --ctest "${CMAKE_CTEST_COMMAND}"
            --cc "${CMAKE_C_COMPILER}" --cxx "${CMAKE_CXX_COMPILER}"
            --clang "${compiler_CWHIP_CLANG_EXECUTABLE}"
            "--gtk=${CWHIP_GTK}" "--sourceview=${CWHIP_GTK_SOURCEVIEW}"
            "--editor=${CWHIP_BUILD_CEDIT}" "--debugger=${CWHIP_BUILD_CDBG}"
            "--cmacros=${CWHIP_BUILD_CMACROS}"
        DEPENDS ${test_all_dependencies}
        USES_TERMINAL VERBATIM)
else()
    add_custom_target(test-all
        COMMAND "${CMAKE_COMMAND}" -E echo "test-all requires configuring with BUILD_TESTING=ON"
        COMMAND "${CMAKE_COMMAND}" -E false VERBATIM)
endif()
include(cmake/Clean.cmake)
message(STATUS "Workspace executables: ${workspace_public_bin} (private stage: ${workspace_stage}); website is opt-in")
