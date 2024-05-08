cmake_minimum_required(VERSION 3.19)

project(LunarLander1969
  LANGUAGES Fortran)

enable_testing()

add_executable(lunar-lander lunar.f90)

add_test(NAME basic
COMMAND ${CMAKE_COMMAND}
  -Dexe:FILEPATH=$<TARGET_FILE:lunar-lander>
  -P ${CMAKE_CURRENT_SOURCE_DIR}/test/test_stdin.cmake
)
set_property(TEST basic PROPERTY PASS_REGULAR_EXPRESSION "GOOD LANDING")

file(GENERATE OUTPUT .gitignore CONTENT "*")
