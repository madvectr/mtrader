cmake_minimum_required(VERSION 3.14)
project(OrderMatchingSystem VERSION 0.1.0 LANGUAGES CXX)

# Use C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add include directories
include_directories($(PROJECT_SOURCE_DIR)/include)

# Find dependencies
find_package(GTest REQUIRED)
find_package(Boost COMPONENTS system REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(spdlog REQUIRED)

# Add subdirectories
add_subdirectory(src)
add_subdirectory(tests)
