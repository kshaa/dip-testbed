module main_flashes_and_blocks(
	// Clock pin
	input CLK,

	// Counter
	input flipper,
	input tick,

	// Buttons
	input button_pressed,
	input [7:0] button_index,

	// Display contents
	output [511:0] display
);
	// Coordinate system w/ two points controlled by buttons
	reg r_indexes_changed = 0;
	reg [7:0] a_index = 9;
	parameter A_LEFT = 8;
	parameter A_RIGHT = 10;
	parameter A_UP = 1;
	parameter A_DOWN = 9;
	reg [7:0] b_index = 14;
	parameter B_LEFT = 11;
	parameter B_RIGHT = 13;
	parameter B_UP = 4;
	parameter B_DOWN = 12;
	
	always @(posedge CLK)
	begin
		if (button_pressed) begin
			if (button_index == A_LEFT && (a_index % 8) > 0) begin
				a_index <= a_index - 1;
			end else if (button_pressed && button_index == A_RIGHT && (a_index % 8) < 7) begin
				a_index <= a_index + 1;
			end else if (button_pressed && button_index == A_UP && (a_index / 8) > 0) begin
				a_index <= a_index - 8;
			end else if (button_pressed && button_index == A_DOWN && (a_index / 8) < 7) begin
				a_index <= a_index + 8;
			end else if (button_index == B_LEFT && (b_index % 8) > 0) begin
				b_index <= b_index - 1;
			end else if (button_pressed && button_index == B_RIGHT && (b_index % 8) < 7) begin
				b_index <= b_index + 1;
			end else if (button_pressed && button_index == B_UP && (b_index / 8) > 0) begin
				b_index <= b_index - 8;
			end else if (button_pressed && button_index == B_DOWN && (b_index / 8) < 7) begin
				b_index <= b_index + 8;
			end 
			// Trigger display change
			r_indexes_changed <= 1;
		end else if (display_logic_changed) begin
			// If button unpressed, remember to toggle off display changes
			r_indexes_changed <= 0;
		end
	end

	// Design a display with some flipping bits in three corners
	wire display_logic_changed = tick || r_indexes_changed;
	reg [511:0] r_display = 0; // 64 bytes
	integer display_iterator = 0;
	always @(posedge CLK)
	begin
		for (display_iterator = 0; display_iterator < 64; display_iterator = display_iterator + 1)
			if (display_logic_changed) begin
				if (a_index == display_iterator) begin
					r_display[display_iterator * 8 +: 8] <= 8'b00111111;
				end else if (b_index == display_iterator) begin
					r_display[display_iterator * 8 +: 8] <= 8'b00010101;
				end else if (0 == display_iterator && flipper) begin
					r_display[display_iterator * 8 +: 8] <= 8'b00110000;
				end else if (7 == display_iterator && flipper) begin
					r_display[display_iterator * 8 +: 8] <= 8'b00001100;
				end else if (56 == display_iterator && flipper) begin
					r_display[display_iterator * 8 +: 8] <= 8'b00000011;
				end else begin
					r_display[display_iterator * 8 +: 8] <= 8'b00000000;
				end
			end
	end

	// Assign outputs
	assign display = r_display;
endmodule
