file(GLOB_RECURSE sdk_inputs CONFIGURE_DEPENDS
    "${CMAKE_SOURCE_DIR}/compiler/include/*"
    "${CMAKE_SOURCE_DIR}/compiler/builtin/*"
    "${CMAKE_SOURCE_DIR}/compiler/stdlib/*")

foreach(app cedit cdbg)
    if(NOT CWHIP_GTK_SOURCEVIEW OR
       (app STREQUAL "cedit" AND NOT CWHIP_BUILD_CEDIT) OR
       (app STREQUAL "cdbg" AND NOT CWHIP_BUILD_CDBG))
        add_custom_target(${app}
            COMMAND "${CMAKE_COMMAND}" "-DAPP=${app}" -P "${CMAKE_CURRENT_LIST_DIR}/Unavailable.cmake"
            VERBATIM)
        message(STATUS "${app} unavailable: disabled or GTK 4 >= 4.10 / GtkSourceView 5 bindings unavailable")
        continue()
    endif()
    if(app STREQUAL "cedit")
        set(app_source "${CMAKE_SOURCE_DIR}/editor/src")
    else()
        set(app_source "${CMAKE_SOURCE_DIR}/debugger/src")
    endif()
    set(app_project "${CMAKE_BINARY_DIR}/apps/${app}")
    file(MAKE_DIRECTORY "${app_project}/home" "${app_project}/xdg" "${app_project}/modules")
    set(app_environment ${workspace_environment}
        "HOME=${app_project}/home" "XDG_CONFIG_HOME=${app_project}/xdg")
    file(GLOB_RECURSE app_inputs CONFIGURE_DEPENDS "${app_source}/*")
    file(GENERATE OUTPUT "${app_project}/inputs.txt"
        CONTENT "SDK=${sdk_inputs}\nAPP=${app_inputs}\n")
    set(app_rules "${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_SOURCE_DIR}/CMakeLists.txt"
        "${app_project}/inputs.txt")
    add_custom_command(
        OUTPUT "${app_project}/cwhip-pkg.toml" "${app_project}/cwhip-pkg.lock"
        COMMAND "${CMAKE_COMMAND}" -E rm -f
            "${app_project}/cwhip-pkg.toml" "${app_project}/cwhip-pkg.lock"
        COMMAND ${app_environment} "${Python3_EXECUTABLE}"
            "${workspace_bin}/cwhip-pkg" init "${app_project}"
        DEPENDS cwhip "${resource_stamp}" "${sqlite_archive}" "${gtk_archive}"
            "${workspace_bin}/cwhip-pkg" ${sdk_inputs} ${app_rules}
        COMMENT "Locking ${app}'s private staged packages"
        VERBATIM)
    set(app_native)
    set(app_native_deps)
    set(app_archives "${runtime_archive}" "${gtk_archive}")
    if(app STREQUAL "cedit")
        set(app_output "${workspace_bin}/cedit.bin")
        list(APPEND app_archives "${sqlite_archive}")
        add_executable(cedit_launcher "${app_source}/launcher.c")
        set_target_properties(cedit_launcher PROPERTIES OUTPUT_NAME cedit
            RUNTIME_OUTPUT_DIRECTORY "${workspace_bin}"
            C_STANDARD 11 C_STANDARD_REQUIRED ON)
        add_dependencies(cedit_launcher cwhip)
    else()
        set(app_output "${workspace_bin}/cdbg")
        add_custom_command(OUTPUT "${app_project}/values.h"
            COMMAND "${Python3_EXECUTABLE}" "${app_source}/embed_values.py"
                "${app_source}/values.py" "${app_project}/values.h"
            DEPENDS "${app_source}/embed_values.py" "${app_source}/values.py"
            VERBATIM)
        add_library(cdbg_terminal OBJECT "${app_source}/terminal.c" "${app_project}/values.h")
        target_include_directories(cdbg_terminal PRIVATE
            "${workspace_stage}/include" "${app_project}")
        add_dependencies(cdbg_terminal cwhip)
        set_property(TARGET cdbg_terminal PROPERTY C_STANDARD 11)
        set(app_native $<TARGET_OBJECTS:cdbg_terminal>)
        set(app_native_deps cdbg_terminal ${app_native})
    endif()
    add_custom_command(OUTPUT "${app_output}"
        COMMAND "${CMAKE_COMMAND}" -E rm -rf "${app_project}/src"
        COMMAND "${CMAKE_COMMAND}" -E copy_directory "${app_source}" "${app_project}/src"
        COMMAND ${app_environment} "${workspace_compiler}" "${app_project}/src/${app}.cw"
            -M "${workspace_modules}" -o "${app_output}" ${app_native}
        DEPENDS cwhip "${workspace_compiler}" ${app_archives} "${resource_stamp}"
            ${sdk_inputs} ${app_inputs} ${app_rules} ${app_native_deps}
            "${app_project}/cwhip-pkg.toml" "${app_project}/cwhip-pkg.lock"
        WORKING_DIRECTORY "${app_project}"
        COMMENT "Building external ${app}"
        VERBATIM)
    set(app_public_names ${app})
    if(app STREQUAL "cedit")
        list(APPEND app_public_names cedit.bin)
    endif()
    add_custom_target(${app} ALL
        COMMAND ${workspace_publish} --names ${app_public_names}
        DEPENDS "${app_output}" VERBATIM)
    if(app STREQUAL "cedit")
        add_dependencies(cedit cedit_launcher)
    endif()
endforeach()
