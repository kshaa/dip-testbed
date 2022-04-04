module v_rx_text #(
	// What is the chunk type
	parameter [7:0] INTERFACE_RX_CHUNK_TYPE = 5,
	// The size of the chunk in bytes (maximum chunk size essentially)
	parameter RX_CONTENT_BUFFER_BYTE_SIZE = 33,
	// How many bits needed to index the whole buffer
	parameter RX_CONTENT_BUFFER_INDEX_SIZE = 32
)(
	// clock pin
	input CLK,

	// chunked RX inputs
	input [7:0] rx_chunk_type,
	input [(RX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:0] rx_chunk_bytes,
	input [RX_CONTENT_BUFFER_INDEX_SIZE - 1:0] rx_chunk_byte_size,
	input rx_is_chunk_ready,

	// last received text
	output [(RX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:0] rx_text_bytes,
	output [RX_CONTENT_BUFFER_INDEX_SIZE - 1:0] rx_text_size,
	output rx_is_text_ready
);
	// The RX chunk type
	reg [7:0] r_rx_chunk_type = INTERFACE_RX_CHUNK_TYPE;
	// What's the last received text
	reg [((RX_CONTENT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] r_rx_text_bytes;
	reg [RX_CONTENT_BUFFER_INDEX_SIZE - 1:0] r_rx_text_size;

	// Copy button index when available
	parameter R_VTEXT_STATE_SIZE = 1;
	parameter R_VTEXT_IDLE = 0;
	parameter R_VTEXT_RECEIVED = 1;
	reg [R_VTEXT_STATE_SIZE - 1:0] r_vtext_state = R_VTEXT_IDLE;

	always @(posedge CLK)
	begin
		case (r_vtext_state)
			R_VTEXT_IDLE: begin
				if (rx_is_chunk_ready && 
					rx_chunk_type == r_rx_chunk_type && 
					rx_chunk_byte_size >= 1 &&
					rx_chunk_bytes[7:0] <= 32) begin
					r_rx_text_bytes[((RX_CONTENT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] <= rx_chunk_bytes[(RX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:8];
					r_rx_text_size[7:0] <= rx_chunk_bytes[7:0];
					r_vtext_state <= R_VTEXT_RECEIVED;
				end
			end
			R_VTEXT_RECEIVED: begin
				r_vtext_state <= R_VTEXT_IDLE;
			end
		endcase
	end

	// Outputs
	assign rx_text_bytes = r_rx_text_bytes;
	assign rx_text_size = r_rx_text_size;
	assign rx_is_text_ready = r_vtext_state == R_VTEXT_RECEIVED;
endmodule
