add_library(matching_engine
    matching_engine/order_book.cpp
)

target_include_directories(matching_engine PUBLIC
    ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(matching_engine PRIVATE
    spdlog::spdlog
    nlohmann_json::nlohmann_json
)