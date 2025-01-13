cmake_minimum_required(VERSION 3.10)
project(ps3eye_virtual_camera)

# Force Visual Studio generator
set(CMAKE_GENERATOR "Visual Studio 17 2022" CACHE INTERNAL "" FORCE)
set(CMAKE_GENERATOR_PLATFORM "x64" CACHE INTERNAL "" FORCE)

# Imposta il C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Aggiungi le definizioni per Windows
add_definitions(-DUNICODE -D_UNICODE -DWIN32 -D_WINDOWS)

# Trova Windows SDK
if(NOT DEFINED WindowsSDK_DIR)
    get_filename_component(WindowsSDK_DIR
        "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows Kits\\Installed Roots;KitsRoot10]"
        ABSOLUTE CACHE)
endif()

# Trova l'ultima versione disponibile del SDK
file(GLOB WindowsSDK_Versions
    LIST_DIRECTORIES true
    "${WindowsSDK_DIR}/Include/*"
)
list(SORT WindowsSDK_Versions ORDER DESCENDING)
list(GET WindowsSDK_Versions 0 WindowsSDK_LatestVersion)
get_filename_component(WindowsSDK_LatestVersion "${WindowsSDK_LatestVersion}" NAME)

# Imposta i percorsi per DirectShow
set(DIRECTSHOW_INCLUDE_DIR "${WindowsSDK_DIR}/Include/${WindowsSDK_LatestVersion}/um")
set(STRMIIDS_LIBRARY "${WindowsSDK_DIR}/Lib/${WindowsSDK_LatestVersion}/um/x64/strmiids.lib")

# Verifica che i file esistano
if(NOT EXISTS "${DIRECTSHOW_INCLUDE_DIR}/dshow.h")
    message(FATAL_ERROR "DirectShow headers not found in ${DIRECTSHOW_INCLUDE_DIR}")
endif()
if(NOT EXISTS "${STRMIIDS_LIBRARY}")
    message(FATAL_ERROR "strmiids library not found at ${STRMIIDS_LIBRARY}")
endif()

# Aggiungi la DLL
add_library(ps3eye_virtual_camera SHARED
    virtual_camera.cpp
)

# Imposta le proprietà della DLL
set_target_properties(ps3eye_virtual_camera PROPERTIES
    PREFIX ""
    OUTPUT_NAME "ps3eye_virtual_camera"
)

# Includi le directory necessarie
target_include_directories(ps3eye_virtual_camera PRIVATE
    ${DIRECTSHOW_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Collega le librerie necessarie
target_link_libraries(ps3eye_virtual_camera PRIVATE
    ${STRMIIDS_LIBRARY}
    ole32
    uuid
)
