foreach(app cmacros cedit cdbg)
    if((app STREQUAL "cmacros" AND NOT CWHIP_BUILD_CMACROS) OR
       (app STREQUAL "cedit" AND
        (NOT CWHIP_GTK_SOURCEVIEW OR NOT CWHIP_BUILD_CEDIT)) OR
       (app STREQUAL "cdbg" AND
        (NOT CWHIP_GTK_SOURCEVIEW OR NOT CWHIP_BUILD_CDBG)))
        add_custom_target(${app}
            COMMAND "${CMAKE_COMMAND}" "-DAPP=${app}" -P "${CMAKE_CURRENT_LIST_DIR}/Unavailable.cmake"
            VERBATIM)
        if(app STREQUAL "cmacros")
            message(STATUS "cmacros unavailable: disabled with CWHIP_BUILD_CMACROS=OFF")
        else()
            message(STATUS "${app} unavailable: disabled or GTK 4 >= 4.10 / GtkSourceView 5 bindings unavailable")
        endif()
        continue()
    endif()
    if(app STREQUAL "cmacros")
        set(app_source "${CMAKE_SOURCE_DIR}/cmacros")
        set(app_names cmacros)
        set(app_configure "${CMAKE_COMMAND}" -E env "CWHIP_SDK=${workspace_stage}"
            "${CMAKE_COMMAND}")
        set(app_output_directories
            "-DCWHIP_BIN_DIR=${CMAKE_BINARY_DIR}/apps/cmacros/bin"
            "-DCWHIP_LIB_DIR=${CMAKE_BINARY_DIR}/apps/cmacros/lib")
    elseif(app STREQUAL "cedit")
        set(app_source "${CMAKE_SOURCE_DIR}/editor")
        set(app_names cedit cedit.bin)
        set(app_configure "${CMAKE_COMMAND}")
        set(app_output_directories)
    else()
        set(app_source "${CMAKE_SOURCE_DIR}/debugger")
        set(app_names cdbg)
        set(app_configure "${CMAKE_COMMAND}")
        set(app_output_directories)
    endif()
    set(app_build "${CMAKE_BINARY_DIR}/apps/${app}")
    add_custom_target(${app} ALL
        COMMAND ${app_configure} -S "${app_source}" -B "${app_build}"
            -G "${CMAKE_GENERATOR}"
            "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
            "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
            "-DCMAKE_PREFIX_PATH=${workspace_stage}"
            "-DCwhip_DIR=${workspace_stage}/lib/cmake/Cwhip"
            "-DCMAKE_INSTALL_PREFIX=${workspace_stage}"
            "-DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
            "-DBUILD_TESTING=${BUILD_TESTING}" ${app_output_directories}
        COMMAND "${CMAKE_COMMAND}" --build "${app_build}" --config "$<CONFIG>"
        COMMAND "${CMAKE_COMMAND}" -E env --unset=DESTDIR
            "${CMAKE_COMMAND}" --install "${app_build}" --config "$<CONFIG>"
        COMMAND ${workspace_publish} --names ${app_names}
        DEPENDS cwhip ${workspace_jobserver} USES_TERMINAL VERBATIM)
endforeach()
