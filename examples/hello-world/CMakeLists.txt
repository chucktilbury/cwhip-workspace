cmake_minimum_required(VERSION 3.24)
project(hello_world LANGUAGES C)
find_package(Cwhip 0.0.1 EXACT CONFIG REQUIRED)
cwhip_add_program(hello SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/hello.cw")
