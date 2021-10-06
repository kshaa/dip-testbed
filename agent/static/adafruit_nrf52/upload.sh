#!/usr/bin/env bash

# Stricter scripting: https://explainshell.com/explain?cmd=set+-euxo+pipefail
set -euo pipefail

# Script usage help
usage() {
    echo 'usage: -d "/dev/ttyUSB0" -f "/home/user/code/project/firmware.hex"'
    echo '  -d  Serial device file path'
    echo '  -b  Serial device baud rate (default: 115200)'
    echo '  -f  Firmware hex file path'
    echo '  -v  Enable verbose mode with tracing'
    exit 1
}

# Flag parsing sourced from: https://google.github.io/styleguide/shellguide.html
# also from: https://stackoverflow.com/a/11279500/10806216
device=""
baudrate="115200"
firmwarehex=""
verbose="false"
while getopts 'd:b:f:v' flag; do
  case "${flag}" in
    d) device="${OPTARG}" ;;
    b) baudrate="${OPTARG}" ;;
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

# Validate serial device provided
if [ -z "${device}" ]; then
   echo "Serial device not provided."
   usage
fi

# Validate serial device exists
if [ ! -e "${device}" ]; then
   echo "Serial device '${device}' does not exist."
   exit 1
fi

# Upload firmware to device
tmpdir="$(mktemp -d)"
dfupackage="${tmpdir}/firmware-package.zip"
adafruit-nrfutil dfu genpkg --dev-type 0x0052 --application "${firmwarehex}" "${dfupackage}"
adafruit-nrfutil dfu serial --package "${dfupackage}" -p "${device}" -b "${baudrate}"
rm -rf "${tmpdir}"
