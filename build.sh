#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Backend build
./backend/build.sh &
WEB_BUILD_PID="$!"

# Client build
./client/build_docker.sh &
CLIENT_BUILD_PID="$!"

# Docs build
./docs/build.sh &
DOCS_BUILD_PID="$!"

# Wait for builds
wait "${WEB_BUILD_PID}"
wait "${CLIENT_BUILD_PID}"
wait "${DOCS_BUILD_PID}"
