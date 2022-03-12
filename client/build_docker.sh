#!/usr/bin/env bash

# Fail hard if anything here fails
set -e

# Run script from script source directory
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}"

# Remove old builds
rm -rf docker/
rm -rf dist/

## Build amd64 & arm64 in docker w/ buildx i.e. moby/buildkit i.e. QEMU
## Multi-platform docs: https://github.com/moby/buildkit/blob/master/docs/multi-platform.md
export TARGET_PLATFORMS=linux/arm64,linux/amd64
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker buildx create --name multiarch --driver docker-container --use || true
docker buildx build \
  --platform "${TARGET_PLATFORMS}" \
  -o type=local,dest=docker \
  .

# Create dist
mkdir dist
mv docker/linux_arm64/app/dist/dip_client dist/dip_client_arm64
mv docker/linux_amd64/app/dist/dip_client dist/dip_client_amd64
