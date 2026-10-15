# Unix Makefiles includes cmake_clean_<language>.cmake after each target's
# native clean rules. A non-default object target supplies an unconditional
# C-language clean hook, including with BUILD_TESTING=OFF and no GUI targets.
file(WRITE "${CMAKE_BINARY_DIR}/workspace-clean-hook.c" "/* Clean-rule language anchor. */\n")
add_library(workspace_clean_hook OBJECT EXCLUDE_FROM_ALL
    "${CMAKE_BINARY_DIR}/workspace-clean-hook.c")
configure_file("${CMAKE_CURRENT_LIST_DIR}/CleanHook.cmake.in"
    "${CMAKE_BINARY_DIR}/CMakeFiles/workspace_clean_hook.dir/cmake_clean_C.cmake" @ONLY)
