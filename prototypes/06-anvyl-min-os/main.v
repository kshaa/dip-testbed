// Import kshaa's UART-based MinOS
`include "min_os.v"

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
	// Design a counter:
	// - r_ticks is incremented on every clock cycle
	// - r_virtual_leds is incremented every time r_ticks reaches sleep_ticks
	// - every time r_virtual_leds is incremented, r_ticks is reset
	reg [7:0] r_virtual_leds = 0; 
	parameter sleep_ticks = 32'd100000000;
	reg [31:0] r_ticks = 0;
	always @(posedge CLK)
	begin
		if (r_ticks < sleep_ticks) begin
			// Tick clock
			r_ticks = r_ticks + 1;
		end else if (r_ticks == sleep_ticks) begin
			// Tick clock
			r_ticks = r_ticks + 1;
			// Increment counter
			r_virtual_leds <= r_virtual_leds + 1;
		end else if (r_ticks > sleep_ticks) begin
			// Reset clock
			r_ticks = 0;
		end
	end

	// Instantiate kshaa's UART-based MinOS:
	// - Assign counter value to virtual MinOS LEDs
	min_os min_os_instance (
		.CLK(CLK),
		.T19(T19),
		.T20(T20),
		.LEDS(r_virtual_leds)
	);

	// Assign counter value to physical LEDs
	assign LD0 = r_virtual_leds[0];
	assign LD1 = r_virtual_leds[1];
	assign LD2 = r_virtual_leds[2];
	assign LD3 = r_virtual_leds[3];
	assign LD4 = r_virtual_leds[4];
	assign LD5 = r_virtual_leds[5];
	assign LD6 = r_virtual_leds[6];
	assign LD7 = r_virtual_leds[7];
endmodule
