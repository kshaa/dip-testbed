`timescale 1ns / 1ps

module bit_shift_controller #(
	parameter START_BITS = 8'b00010000
)(
	input [23:0] buttons,
	output [7:0] bits
);
	reg [7:0] r_bits = START_BITS;
	assign bits = r_bits;
	wire sensitivity = buttons != 0;
	always @(posedge sensitivity)
	begin
		if (buttons[0] == 1 && r_bits[0] != 1) begin
			r_bits = r_bits << 1;
		end else if (buttons[1] == 1 && r_bits[7] != 1) begin
			r_bits = r_bits >> 1;
		end else if (buttons[2] == 1) begin
			r_bits = 8'b00010000;
		end else if (buttons[3] == 1) begin
			r_bits = 8'b00101000;
		end else if (buttons[4] == 1) begin
			r_bits = 8'b01010101;
		end else if (buttons[5] == 1) begin
			r_bits = 8'b10101010;
		end else if (buttons[6] == 1) begin
			r_bits = 8'b00000000;
		end else if (buttons[7] == 1) begin
			r_bits = 8'b11111111;
		end else if (buttons[8] == 1) begin
			r_bits = 8'b00000001;
		end else if (buttons[9] == 1) begin
			r_bits = 8'b00000010;
		end else if (buttons[10] == 1) begin
			r_bits = 8'b00000100;
		end else if (buttons[11] == 1) begin
			r_bits = 8'b00001000;
		end else if (buttons[12] == 1) begin
			r_bits = 8'b00010000;
		end else if (buttons[13] == 1) begin
			r_bits = 8'b00100000;
		end else if (buttons[14] == 1) begin
			r_bits = 8'b01000000;
		end else if (buttons[15] == 1) begin
			r_bits = 8'b10000000;
		end
	end
endmodule
