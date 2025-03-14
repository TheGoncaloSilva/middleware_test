#!/bin/bash

fastddsgen -python SimpleMessage.idl

if [ -d "build" ]; then
    cd build
else
    mkdir build && cd build
fi

cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/ -DBUILD_SHARED_LIBS=ON .
cmake --build .
cd ..

# Remove unnecessary files
rm CMakeLists.txt
find . -maxdepth 1 -type f -name "*SimpleMessage*" ! -name "SimpleMessage.idl" -exec rm {} +
