#!/usr/bin/env bash

# Stricter scripting: https://explainshell.com/explain?cmd=set+-euxo+pipefail
set -euo pipefail

# Script usage help
usage() {
    echo 'Streams a V4L2 video stream on a given TCP socket using VLC'
    echo 'usage: -d /dev/video0 -w 1280 -h 720 -v 50 -s 44100 -a 50 -p 8081'
    echo '  -d  V4L2 device path'
    echo '  -w  Video width in pixels'
    echo '  -h  Video height in pixels'
    echo '  -v  Video buffer size'
    echo '  -s  Audio sample rate'
    echo '  -a  Audio buffer size'
    echo '  -p  TCP port for video stream socket'
}

# Flag parsing sourced from: https://google.github.io/styleguide/shellguide.html
# also from: https://stackoverflow.com/a/11279500/10806216
video_device="/dev/video0"
video_width="1280"
video_height="720"
video_buffer_size="50"
audio_sample_rate="44100"
audio_buffer_size="50"
port="8081"
while getopts 'd:w:h:v:s:a:p:' flag; do
  case "${flag}" in
    d) video_device="${OPTARG}" ;;
    w) video_width="${OPTARG}" ;;
    h) video_height="${OPTARG}" ;;
    v) video_buffer_size="${OPTARG}" ;;
    s) audio_sample_rate="${OPTARG}" ;;
    a) audio_buffer_size="${OPTARG}" ;;
    p) port="${OPTARG}" ;;
    *) usage >&2 && exit 1 ;;
  esac
done

# Print usage
usage

# Env dump
echo "Video device: ${video_device}"
echo "Video width: ${video_width}"
echo "Video height: ${video_height}"
echo "Video buffer size: ${video_buffer_size}"
echo "Audio sample rate: ${audio_sample_rate}"
echo "Audio buffer size: ${audio_buffer_size}"
echo "Port: ${port}"

# Start video stream
echo "Starting video stream..."
vlc v4l2:// \
  :input-slave=alsa:// \
  :v4l2-standard=1 \
  :v4l2-dev=${video_device} \
  :v4l2-width=${video_width} \
  :v4l2-height=${video_height} \
  :sout="#transcode{vcodec=theo,vb=${video_buffer_size},acodec=vorb,ab=${audio_buffer_size},channels=2,samplerate=${audio_sample_rate}}:http{dst=:${port}/webcam.ogg}" \
  -I dummy
