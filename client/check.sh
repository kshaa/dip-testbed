#!/usr/bin/env bash

# Fail hard if anything here fails and debug every call
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Check everything
echo "Checking unit tests"
./test.sh
echo "Checking lint"
./lint.sh
echo "Checking static types"
./typecheck.sh
