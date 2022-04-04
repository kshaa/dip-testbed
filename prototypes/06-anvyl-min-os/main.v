// Import kshaa's UART-based MinOS
`include "min_os.v"
// Arbitrary logic for per-second counter
`include "main_counter.v"
// Arbitrary logic for flashing light and moving block display 
`include "main_flashes_and_blocks.v"
// Arbitrary logic for copying and pasting incoming text to output
`include "main_echo_text.v"

// Define a UART reader/transmitter FPGA program
module main(
	// Clock pin
	input CLK,
	
	// UART RX/TX pins
	input T19,
	output T20,
	
	// Physical GPIO: LEDs
	output LD0,
	output LD1,
	output LD2,
	output LD3,
	output LD4,
	output LD5,
	output LD6,
	output LD7
);
	// Counter instance
	wire [7:0] counter;
	wire flipper;
	wire tick;
	main_counter main_counter_instance (
		.CLK(CLK),
		.counter(counter),
		.flipper(flipper),
		.tick(tick)
	);

	// Design an output byte to render to virtual and physical LEDs
	// If any switch bit is on, the switch is the output
	// If all switches are off, the counter is the output
	wire [7:0] output_byte = switches == 0 ? counter : switches;

	// Design a coordinate system w/ two points controlled by buttons
	wire [511:0] display;
	wire [7:0] mos_button_index;
	wire mos_button_pressed;
	main_flashes_and_blocks main_flashes_and_blocks_instance(
		.CLK(CLK),
		.flipper(flipper),
		.tick(tick),
		.button_pressed(mos_button_pressed),
		.button_index(mos_button_index),
		.display(display)
	);

	// Echo back received text
	wire [(32 * 8) - 1:0] rx_text_bytes;
	wire [8 - 1:0] rx_text_size;
	wire rx_is_text_ready;
	wire [(32 * 8) - 1:0] tx_text_bytes;
	wire [8 - 1:0] tx_text_size;
	main_echo_text main_echo_text_instance(
		.rx_text_bytes(rx_text_bytes),
		.rx_text_size(rx_text_size),
		.rx_is_text_ready(rx_is_text_ready),
		.tx_text_bytes(tx_text_bytes),
		.tx_text_size(tx_text_size)
	);

	// Instantiate kshaa's UART-based MinOS:
	// - with output_byte assigned to virtual interface "leds"
	// - with r_display bytes assigned to virtual interface "display"
	// - with switches sourced out of the virtual interface "switches"
	wire [7:0] switches;
	min_os min_os_instance(
		.CLK(CLK),
		.T19(T19),
		.T20(T20),
		.leds(output_byte),
		.display(display),
		.switches(switches),
		.button_index(mos_button_index),
		.button_pressed(mos_button_pressed),
		.rx_text_bytes(rx_text_bytes),
		.rx_text_size(rx_text_size),
		.rx_is_text_ready(rx_is_text_ready),
		.tx_text_bytes(tx_text_bytes),
		.tx_text_size(tx_text_size)
	);

	// Assign output_byte value to physical LEDs
	assign LD0 = output_byte[0];
	assign LD1 = output_byte[1];
	assign LD2 = output_byte[2];
	assign LD3 = output_byte[3];
	assign LD4 = output_byte[4];
	assign LD5 = output_byte[5];
	assign LD6 = output_byte[6];
	assign LD7 = output_byte[7];
endmodule
