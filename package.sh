#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Prepare output
rm -rf dist/
mkdir dist/

# Artefact compilation
## Copy user-friendly docs
cp -rf docs/dist/* dist/
rm -rf dist/dist/
mkdir dist/dist/
## Copy binaries
cp -rf backend/web/target/universal/web-0.1.0-SNAPSHOT.zip dist/dist/dip_server.zip
cp -rf client/dist/* dist/dist/

# Copy all of this into user-friendly dist repo if it exists
if [ -d "../dip-testbed-dist" ] 
then
    rm -rf ../dip-testbed-dist/*
    rm -rf ../dip-testbed-dist/.gitignore
    cp -rf dist/* ../dip-testbed-dist/
    cp -rf .gitignore ../dip-testbed-dist/.gitignore
fi
