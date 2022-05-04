module main_counter(
	// Clock pin
	input CLK,
	// Counter
	output [7:0] counter,
	// Per-second flipper
	output flipper,
	// Per-second tick signal
	output tick
);
	// Design a counter:
	// - r_ticks is incremented on every clock cycle
	// - r_counter is incremented every time r_ticks reaches sleep_ticks
	// - r_flipper is flipped every time r_ticks reaches sleep_ticks
	// - every time r_counter is incremented, r_ticks is reset
	reg [7:0] r_counter = 0; 
	reg r_flipper = 0;
	reg r_tick = 0;
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
			r_counter <= r_counter + 1;
			// Flip flipper
			r_flipper <= !r_flipper;
			// Trigger display re-draw
			r_tick <= 1;
		end else if (r_ticks > sleep_ticks) begin
			// Reset clock
			r_ticks = 0;
			// Stop display update
			r_tick <= 0;
		end
	end

	// Assign outputs
	assign counter = r_counter;
	assign flipper = r_flipper;
	assign tick = r_tick;
endmodule
