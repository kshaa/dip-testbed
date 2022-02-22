#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR

# Prepare tag
TAG="$1"
if [ -z "${TAG}" ]
then
    echo "First parameter must be tag to be published, see current tags:"
    git tag -l --sort=v:refname
    exit 1
fi

# Publish auth check
if gh auth status
then
    echo "Publishing under tag ${TAG}"
else
    exit 1
fi

# Publish version check
if gh release view "${TAG}"
then
    echo "Version already exists, removing old version"
    gh release delete "${TAG}"
fi

# Release info
echo "The following files will be in the release:"
ls -la dist/dist

# Create release
echo "Creating release ${TAG}"
gh release create "${TAG}" dist/dist/*
