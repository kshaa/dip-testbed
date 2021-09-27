#!/usr/bin/env bash

# Stricter bash scripting: https://explainshell.com/explain?cmd=set+-euxo+pipefail
set -euo pipefail

# Script usage help
usage() {
    echo 'usage: -d "/dev/ttyUSB0"'
    echo '  -d  Serial device file path'
    echo '  -b  Serial device baud rate (default: 115200)'
    echo '  -v  Enable verbose mode with tracing'
    exit 1
}

# Flag parsing sourced from: https://google.github.io/styleguide/shellguide.html
device=""
baudrate="115200"
verbose="false"
while getopts 'd:b:v' flag; do
  case "${flag}" in
    d) device="${OPTARG}" ;;
    b) baudrate="${OPTARG}" ;;
    v) verbose='true' ;;
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

# Validate serial device exists
if [ ! -e "${device}" ]; then
   echo "Serial device '${device}' does not exist."
   exit 1
fi

# Open screen with serial device
screen ${device} ${baudrate}
