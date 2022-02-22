#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}"

# Remove old builds
rm -rf docker/
rm -rf dist/

# Build amd64 locally (supposing that we're building on amd64)
pipenv install && pipenv run ./build.sh &
LOCAL_INSTALL_PID="$!"

## Build amd64 & arm64 in docker w/ buildx i.e. moby/buildkit i.e. QEMU
## Multi-platform docs: https://github.com/moby/buildkit/blob/master/docs/multi-platform.md
export TARGET_PLATFORMS=linux/arm64 #,linux/amd64 # Currently Kivy (used in amd64) doesn't comply with docker builds
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker buildx create --name multiarch --driver docker-container --use || true
docker buildx build \
  --platform "${TARGET_PLATFORMS}" \
  -o type=local,dest=docker \
  .

# Wait for local stuff to finish
wait "${LOCAL_INSTALL_PID}"

# Clean up dist
mv dist/dip_client dist/dip_client_amd64
#mv docker/linux_arm64/app/dist/dip_client dist/dip_client_arm64
mv docker/app/dist/dip_client dist/dip_client_arm64
