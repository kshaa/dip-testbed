YOSYS    ?= yosys
INKSCAPE ?= inkscape

YOSYS_FLAGS ?= -q
# YOSYS_FLAGS ?= -Q -T

# NETLISTSVG = node netlistsvg.js 
NETLISTSVG = netlistsvg
# NETLISTSVG_OPTS = --skin path/to/skin.svg
NETLISTSVG_OPTS = 
NETLISTSVG_DPI = 300

# Simple files are the same flattened as not
SIMPLE_FILES=min_os.v main.v uart_rx.v uart_tx.v v_buttons.v v_display.v v_leds.v v_switches.v uart_rx_typed_chunker.v uart_tx_typed_chunker.v main_counter.v main_flashes_and_blocks.v v_rx_text.v v_tx_text.v main_echo_text.v
# Complex files are different when flattened
COMPLEX_FILES=

ALL_TARGETS= \
	     $(foreach v,$(SIMPLE_FILES) ,$(basename $(v)).simple.all) \
	     $(foreach v,$(COMPLEX_FILES),$(basename $(v)).complex.all)

GET_TOP ?= export TOP=$$(echo $(basename $<));

# Top level diagram
%.json: %.v Makefile
	$(GET_TOP) $(YOSYS) $(YOSYS_FLAGS) -p "prep -top $$TOP; write_json $@" $<

# Split wires, can make it easier for the diagram if nets are split up
%.split.json: %.v Makefile
	$(GET_TOP) $(YOSYS) $(YOSYS_FLAGS) -p "prep -top $$TOP; splitnets; write_json $@" $<

# Flatten the diagram into logic + black boxes
%.flat.json: %.v Makefile
	$(GET_TOP) $(YOSYS) $(YOSYS_FLAGS) -p "prep -top $$TOP -flatten; write_json $@" $<

# Convert logic into "simple logic" - NOT, AND, XOR, etc
%.simplemap.json: %.v Makefile
	$(GET_TOP) $(YOSYS) $(YOSYS_FLAGS) -p "prep -top $$TOP -flatten; cd $$TOP; simplemap; write_json $@" $<

# Use netlistsvg to generate SVG files
%.svg: %.json $(NETLISTSVG_SKIN)
	$(NETLISTSVG) $(NETLISTSVG_OPTS) $< -o $@

# Use inkscape to render the SVG files into PNG files.
%.png: %.svg
	$(INKSCAPE) --export-png $@ --export-dpi $(NETLISTSVG_DPI) $< 2>&1 | grep -v "WARNING: unknown type: s:alias"

# Open the rendered PNG in a file viewer
%.view: %.png
	eog $< &

# Generate all PNGs for simple files
%.simple.all: %.png
	@true

# Generate all PNGS for complex files
%.complex.all: %.png %.split.png %.flat.png %.simplemap.png
	@true

# Build everything!
build.all: $(ALL_TARGETS)
	@true

clean:
	rm -f *.json *.svg *.png

all:
	make clean
	make build.all

.DEFAULT_GOAL := all
.PRECIOUS: %.png
.PHONY: view clean all
