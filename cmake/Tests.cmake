add_test(NAME workspace_diagnostics
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/status.py")
add_test(NAME workspace_python
    COMMAND "${Python3_EXECUTABLE}" -m unittest discover -s "${CMAKE_SOURCE_DIR}/tests" -v)
set(test_work "${CMAKE_BINARY_DIR}/tests")
file(MAKE_DIRECTORY "${test_work}")
add_custom_command(OUTPUT "${test_work}/values.h"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${test_work}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/debugger/src/embed_values.py"
        "${CMAKE_SOURCE_DIR}/debugger/src/values.py" "${test_work}/values.h"
    DEPENDS "${CMAKE_SOURCE_DIR}/debugger/src/embed_values.py"
        "${CMAKE_SOURCE_DIR}/debugger/src/values.py"
    VERBATIM)
add_executable(workspace_terminal_test
    "${CMAKE_SOURCE_DIR}/debugger/tests/test_cdbg_terminal.c"
    "${CMAKE_SOURCE_DIR}/debugger/src/terminal.c" "${test_work}/values.h")
target_include_directories(workspace_terminal_test PRIVATE
    "${CMAKE_SOURCE_DIR}/compiler/include" "${test_work}")
target_compile_options(workspace_terminal_test PRIVATE -UNDEBUG)
set_target_properties(workspace_terminal_test PROPERTIES C_STANDARD 11
    RUNTIME_OUTPUT_DIRECTORY "${test_work}")
add_test(NAME workspace_native_terminal COMMAND workspace_terminal_test)
foreach(check smoke inspector noop)
    add_test(NAME workspace_${check}
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/build_checks.py"
            --mode ${check} --build "${CMAKE_BINARY_DIR}" --cmake "${CMAKE_COMMAND}"
            --clang "${compiler_CWHIP_CLANG_EXECUTABLE}")
endforeach()
set_tests_properties(workspace_noop PROPERTIES RUN_SERIAL TRUE TIMEOUT 180)
set_tests_properties(workspace_inspector PROPERTIES SKIP_RETURN_CODE 77)
add_test(NAME workspace_mi_parser
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/debugger/tests/test_cdbg.py"
        --compiler "${workspace_compiler}" --source "${CMAKE_SOURCE_DIR}/debugger/src/cdbg.cw"
        --work "${test_work}/mi" --group parser)
set_tests_properties(workspace_smoke workspace_inspector workspace_mi_parser PROPERTIES TIMEOUT 120)
set_tests_properties(workspace_diagnostics workspace_python workspace_smoke
    workspace_inspector workspace_noop workspace_mi_parser
    PROPERTIES ENVIRONMENT "PYTHONDONTWRITEBYTECODE=1")
