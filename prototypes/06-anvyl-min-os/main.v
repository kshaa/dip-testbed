// Import kshaa's UART-based MinOS
`include "min_os.v"
// Arbitrary logic for per-second counter
`include "main_counter.v"
// Arbitrary logic for flashing light and moving block display 
`include "main_flashes_and_blocks.v"

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
	main_flashes_and_blocks main_flashes_and_blocks_instance(
		.CLK(CLK),
		.flipper(flipper),
		.tick(tick),
		.button_pressed(button_pressed),
		.button_index(button_index),
		.display(display)
	);

	// Instantiate kshaa's UART-based MinOS:
	// - with output_byte assigned to virtual interface "leds"
	// - with r_display bytes assigned to virtual interface "display"
	// - with switches sourced out of the virtual interface "switches"
	wire [7:0] switches;
	wire [7:0] button_index;
	wire button_pressed;
	min_os min_os_instance (
		.CLK(CLK),
		.T19(T19),
		.T20(T20),
		.leds(output_byte),
		.display(display),
		.switches(switches),
		.button_index(button_index),
		.button_pressed(button_pressed)
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
