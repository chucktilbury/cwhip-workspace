cmake_minimum_required(VERSION 3.24)
project(workspace_external_tests LANGUAGES NONE)
enable_testing()
find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
find_program(XVFB Xvfb)
find_program(GDB gdb)
set(compiler "${COMPILER_STAGE}/bin/cwhip")
set(native "${WORKSPACE_SOURCE}/compiler/stdlib/gtk/0.1.0/native")
set(editor_source "${WORKSPACE_SOURCE}/editor/src/cedit.cw")
set(debugger_source "${ADAPTER}/tools/cdbg/cdbg.cw")
set(editor_arguments --compiler "${compiler}" --clang "${CLANG}"
    --include "${COMPILER_STAGE}/include" --native "${native}"
    --source "${editor_source}" --xvfb "${XVFB}")
if(EDITOR)
    add_test(NAME external_cedit_build COMMAND "${Python3_EXECUTABLE}"
        "${ADAPTER}/editor-tests/test_cedit_build.py"
        --build "${WORKSPACE_BUILD}" --cmake "${CMAKE_COMMAND}"
        --executable "${WORKSPACE_BUILD}/stage/bin/cedit"
        --compiler "${WORKSPACE_BUILD}/stage/bin/cwhip")
    if(HEADLESS)
        foreach(mode binary default_shortcuts)
            set(example_arguments)
            if(mode STREQUAL "binary")
                list(APPEND example_arguments --executable "${WORKSPACE_BUILD}/stage/bin/cedit")
            else()
                list(APPEND example_arguments --default-shortcuts)
            endif()
            add_test(NAME external_cedit_${mode} COMMAND "${Python3_EXECUTABLE}"
                "${WORKSPACE_SOURCE}/compiler/tests/test_examples.py"
                --compiler "${compiler}" --examples "${ADAPTER}/examples"
                --manifest "${WORKSPACE_SOURCE}/compiler/tests/examples.json"
                --work "${CMAKE_BINARY_DIR}/${mode}" --case editor/cedit.cw
                --gtk --sourceview --xvfb "${XVFB}" ${example_arguments})
        endforeach()
        add_test(NAME external_cedit_shortcuts COMMAND "${Python3_EXECUTABLE}"
            "${ADAPTER}/editor-tests/test_cedit_shortcuts.py"
            --executable "${WORKSPACE_BUILD}/stage/bin/cedit" --xvfb "${XVFB}"
            --work "${CMAKE_BINARY_DIR}/shortcuts")
        foreach(group ui migration save invalid)
            add_test(NAME external_cedit_preferences_${group} COMMAND "${Python3_EXECUTABLE}"
                "${ADAPTER}/editor-tests/test_cedit_preferences.py" ${editor_arguments}
                --work "${CMAKE_BINARY_DIR}/preferences-${group}" --group "${group}")
        endforeach()
        foreach(group session switching lifecycle invalid)
            add_test(NAME external_cedit_project_${group} COMMAND "${Python3_EXECUTABLE}"
                "${ADAPTER}/editor-tests/test_cedit_project.py" ${editor_arguments}
                --cmake "${WORKSPACE_SOURCE}/compiler/CMakeLists.txt"
                --work "${CMAKE_BINARY_DIR}/project-${group}" --group "${group}")
        endforeach()
        # These compiler-owned fixture drivers accept an explicit source input,
        # so reuse them on the extracted editor, not its integrated duplicate.
        foreach(driver project_explorer editor_dialogs)
            add_test(NAME external_cedit_${driver} COMMAND "${Python3_EXECUTABLE}"
                "${WORKSPACE_SOURCE}/compiler/tests/test_${driver}.py" ${editor_arguments}
                --work "${CMAKE_BINARY_DIR}/${driver}")
        endforeach()
    else()
        message(STATUS "EXCLUDED: external editor GUI suites (headless dependencies unavailable)")
    endif()
else()
    message(STATUS "EXCLUDED: external editor suites (app or SourceView disabled)")
endif()
if(DEBUGGER)
    set(debugger_arguments --compiler "${compiler}" --source "${debugger_source}")
    add_test(NAME external_cdbg_build COMMAND "${Python3_EXECUTABLE}"
        "${ADAPTER}/tests/test_cdbg.py" ${debugger_arguments}
        --work "${CMAKE_BINARY_DIR}/debugger-build" --group build
        --build "${WORKSPACE_BUILD}" --cmake "${CMAKE_COMMAND}"
        --executable "${WORKSPACE_BUILD}/stage/bin/cdbg")
    add_test(NAME external_cdbg_parser COMMAND "${Python3_EXECUTABLE}"
        "${ADAPTER}/tests/test_cdbg.py" ${debugger_arguments}
        --work "${CMAKE_BINARY_DIR}/debugger-parser" --group parser)
    if(HEADLESS AND GDB)
        add_test(NAME external_cdbg_session COMMAND "${Python3_EXECUTABLE}"
            "${ADAPTER}/tests/test_cdbg.py" ${debugger_arguments}
            --work "${CMAKE_BINARY_DIR}/debugger-session" --group session
            --gdb "${GDB}" --clang "${CLANG}" --xvfb "${XVFB}"
            --executable "${WORKSPACE_BUILD}/stage/bin/cdbg")
    else()
        message(STATUS "EXCLUDED: external debugger sessions (headless dependencies or GDB unavailable)")
    endif()
else()
    message(STATUS "EXCLUDED: external debugger GUI/build suites (app or SourceView disabled)")
endif()
get_property(tests DIRECTORY PROPERTY TESTS)
if(tests)
    set_tests_properties(${tests} PROPERTIES TIMEOUT 600
        ENVIRONMENT "PYTHONDONTWRITEBYTECODE=1")
endif()
