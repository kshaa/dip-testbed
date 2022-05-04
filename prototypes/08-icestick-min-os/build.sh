#!/usr/bin/env bash

top=main
profile=icestick.pcf

rm -rf ${top}.blif ${top}.txt ${top}.bin
yosys -q -p "synth_ice40 -top ${top} -blif ${top}.blif" ${top}.v
arachne-pnr -d 1k -p ${profile} ${top}.blif -o ${top}.txt
icepack ${top}.txt > ${top}.bin
