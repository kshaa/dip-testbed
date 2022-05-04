#!/usr/bin/env bash

# Stricter scripting: https://explainshell.com/explain?cmd=set+-euxo+pipefail
set -euo pipefail

# Script usage help
usage() {
    echo 'usage: -d "i:0x0403:0x6010" -f "/home/user/code/project/firmware.hex"'
    echo '  -d  Device ID (e.g. "i:0x0403:0x6010")'
    echo '  -f  Firmware hex file path'
    echo '  -v  Enable verbose mode with tracing'
    exit 1
}

# Flag parsing sourced from: https://google.github.io/styleguide/shellguide.html
# also from: https://stackoverflow.com/a/11279500/10806216
device=""
firmwarehex=""
verbose="false"
while getopts 'd:f:v' flag; do
  case "${flag}" in
    d) device="${OPTARG}" ;;
    f) firmwarehex="${OPTARG}" ;;
    v) verbose="true" ;;
    *) usage >&2 && exit 1 ;;
  esac
done

# Force required arguments
if [ $# -eq 0 ]; then
    usage
fi

# Enable verbose tracing
if [ "$verbose" == "true" ]; then
    set -x
fi

# Validate firmware provided
if [ -z "${firmwarehex}" ]; then
   echo "Firmware not provided."
   usage
fi

# Validate firmware exists
if [ ! -f "${firmwarehex}" ]; then
   echo "Firmware hex file '${firmwarehex}' does not exist."
   usage
fi

# Validate device name provided
if [ -z "${device}" ]; then
   echo "Device name not provided."
   usage
fi

# Upload firmware to device
tmpdir="$(mktemp -d)"
firmwarehextmp="${firmwarehex}.bit"
cp -rf "${firmwarehex}" "${firmwarehextmp}"
echo "Uploading '${firmwarehextmp}'"
if iceprog -d "${device}" "${firmwarehextmp}"; then
  rm -rf "${tmpdir}"
  rm -rf "${firmwarehextmp}"
  echo "Uploaded firmware"
  exit 0
else
  rm -rf "${tmpdir}"
  rm -rf "${firmwarehextmp}"
  echo "Upload failed, was the firmware a valid program?"
  exit 1
fi

