#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Check linting
pylint *.py
