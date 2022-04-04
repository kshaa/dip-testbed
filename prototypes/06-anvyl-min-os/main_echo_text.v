module main_echo_text(
	input [(32 * 8) - 1:0] rx_text_bytes,
	input [8 - 1:0] rx_text_size,
	input rx_is_text_ready,
	output [(32 * 8) - 1:0] tx_text_bytes,
	output [8 - 1:0] tx_text_size
);
	// Echo back received text
	reg [(32 * 8) - 1:0] r_tx_text_bytes;
	reg [8 - 1:0] r_tx_text_size;
	always @(posedge rx_is_text_ready) begin
		r_tx_text_bytes <= rx_text_bytes;
		r_tx_text_size <= rx_text_size;
	end

	// Outputs
	assign tx_text_bytes = r_tx_text_bytes;
	assign tx_text_size = r_tx_text_size;
endmodule
