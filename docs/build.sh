#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Prepare artefact dir
rm -rf dist
mkdir dist

# Execute build
mkdir dist/docs/
cp -rf ./*.md dist/docs/
cp -rf ./assets dist/docs/assets
cp -rf ../prototypes dist/prototypes  
cp -rf ../README.md dist/README.md  
cp -rf ../.gitignore dist/.gitignore  
cp -rf ./client_install.sh dist/client_install.sh  
