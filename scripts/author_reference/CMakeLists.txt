cmake_minimum_required(VERSION 3.16)
project(flpa_author_reference C CXX)

find_package(igraph 0.9.6 EXACT CONFIG REQUIRED)
add_executable(flpa-author-reference main.c)
target_link_libraries(flpa-author-reference PRIVATE igraph::igraph)
target_compile_features(flpa-author-reference PRIVATE c_std_99)
