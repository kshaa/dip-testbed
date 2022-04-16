// Define a UART reader/transmitter FPGA program
module main(
	input BTN0,
	input BTN1,
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
	reg [7:0] counter;
	wire BTN = BTN0 || BTN1;
	always @(posedge BTN)
	begin
		if (BTN0) begin
			counter <= counter - 1;
		end else if (BTN1) begin
			counter <= counter + 1;
		end
	end

	// Assign counter value to physical LEDs
	assign LD0 = counter[0];
	assign LD1 = counter[1];
	assign LD2 = counter[2];
	assign LD3 = counter[3];
	assign LD4 = counter[4];
	assign LD5 = counter[5];
	assign LD6 = counter[6];
	assign LD7 = counter[7];
endmodule
