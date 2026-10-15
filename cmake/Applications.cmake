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
        set(app_source "${CMAKE_SOURCE_DIR}/editor")
        set(app_names cedit cedit.bin)
    else()
        set(app_source "${CMAKE_SOURCE_DIR}/debugger")
        set(app_names cdbg)
    endif()
    set(app_build "${CMAKE_BINARY_DIR}/apps/${app}")
    add_custom_target(${app} ALL
        COMMAND "${CMAKE_COMMAND}" -S "${app_source}" -B "${app_build}"
            -G "${CMAKE_GENERATOR}"
            "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
            "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
            "-DCMAKE_PREFIX_PATH=${workspace_stage}"
            "-DCwhip_DIR=${workspace_stage}/lib/cmake/Cwhip"
            "-DCMAKE_INSTALL_PREFIX=${workspace_stage}"
            "-DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
            "-DBUILD_TESTING=${BUILD_TESTING}"
        COMMAND "${CMAKE_COMMAND}" --build "${app_build}" --config "$<CONFIG>"
        COMMAND "${CMAKE_COMMAND}" -E env --unset=DESTDIR
            "${CMAKE_COMMAND}" --install "${app_build}" --config "$<CONFIG>"
        COMMAND ${workspace_publish} --names ${app_names}
        DEPENDS cwhip ${workspace_jobserver} USES_TERMINAL VERBATIM)
endforeach()
