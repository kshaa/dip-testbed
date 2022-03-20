// Buffer-based typed chunk sender
module uart_tx_typed_chunker #(
	// The size of the chunk in bytes (maximum chunk size essentially)
	parameter BUFFER_BYTE_SIZE = 3,
	// How many bits needed to index the whole buffer
	parameter BUFFER_INDEX_SIZE = 32
)(
	// Clock pin
	input CLK,
	// Is chunk ready to be sent out
	input is_chunk_ready,
	// How many bytes are filled in the chunk/buffer
	input [BUFFER_INDEX_SIZE - 1:0] chunk_byte_size,
	// State of the last transmission
	input is_tx_done,
	// The buffer i.e. bytes i.e. contents of the chunk 
	input [(BUFFER_BYTE_SIZE * 8) - 1:0] chunk_bytes,
	// An arbitrary identifier for the chunk
	// must not be 0, otherwise buggy behaviour will occur 
	input [7:0] chunk_type,
	// Is the active byte ready to be sent out
	output is_tx_ready,
	// The active byte to be sent out
	output [7:0] tx_data
);
	// Readiness to transmit
	reg r_tx_ready = 0;
	reg [7:0] r_tx_data = 0;

	// Index of the final byte
	reg [BUFFER_INDEX_SIZE - 1:0] r_chunk_final_byte_index = 0;
	
	// Index of the active (to-be-transmitted) byte
	reg [BUFFER_INDEX_SIZE - 1:0] r_chunk_byte_index = 0;

	// If active byte is a null-byte, then it must be escaped
	// This register contains whether we've already escaped this byte
	reg r_did_we_escape_null_already = 0;

	// Registers for sending chunk type
	reg is_type_escape_sent = 0;
	reg is_type_value_sent = 0;

	// FSM states
	parameter R_CHUNKER_STATE_SIZE = 3;
	parameter R_CHUNKER_IDLE = 0;
	parameter R_CHUNKER_LOADING = 1;
	parameter R_CHUNKER_TRIGGERING = 2;
	parameter R_CHUNKER_TRIGGERED = 3;
	parameter R_CHUNKER_TRANSMITTING = 4;
	reg [R_CHUNKER_STATE_SIZE - 1:0] r_chunker_state = R_CHUNKER_IDLE;

	// Byte containing active indexed chunk
	wire [7:0] active_chunk;
	assign active_chunk[0] = chunk_bytes[(r_chunk_byte_index * 8) + 0];
	assign active_chunk[1] = chunk_bytes[(r_chunk_byte_index * 8) + 1];
	assign active_chunk[2] = chunk_bytes[(r_chunk_byte_index * 8) + 2];
	assign active_chunk[3] = chunk_bytes[(r_chunk_byte_index * 8) + 3];
	assign active_chunk[4] = chunk_bytes[(r_chunk_byte_index * 8) + 4];
	assign active_chunk[5] = chunk_bytes[(r_chunk_byte_index * 8) + 5];
	assign active_chunk[6] = chunk_bytes[(r_chunk_byte_index * 8) + 6];
	assign active_chunk[7] = chunk_bytes[(r_chunk_byte_index * 8) + 7];
	
	// FSM implementation
	always @(posedge CLK) begin
		case (r_chunker_state)
			// While in idle mode - wait for the next chunk to be sent
			// if chunk is ready, switch into loading mode
			R_CHUNKER_IDLE: begin
				if (is_chunk_ready == 1) begin
					r_chunker_state <= R_CHUNKER_LOADING;
					r_chunk_final_byte_index <= chunk_byte_size - 1;
				end
			end
			// Load the next byte from the chunk into the UART TX module
			R_CHUNKER_LOADING: begin
				if (!is_type_escape_sent) begin
					// Escaping chunk type
					r_tx_data <= 0;
				end else if (!is_type_value_sent) begin
					// Sending chunk type value
					r_tx_data <= chunk_type;
				end else if (active_chunk == 0 && r_did_we_escape_null_already == 0) begin
					// Escaping a null byte means we just write another null-byte in front of it
					r_tx_data <= 0;
				end else begin
					// If this is not a null-byte, just send it
					r_tx_data <= active_chunk;
				end
				r_chunker_state <= R_CHUNKER_TRIGGERING;
			end
			// Trigger the UART TX module to send the loaded byte
			R_CHUNKER_TRIGGERING: begin
				r_tx_ready <= 1;
				r_chunker_state <= R_CHUNKER_TRIGGERED;
			end
			// Bring back down the UART TX readiness signal
			R_CHUNKER_TRIGGERED: begin
				r_tx_ready <= 0;
				r_chunker_state <= R_CHUNKER_TRANSMITTING;
			end
			// Wait until the UART TX module is finished
			// then either load and send the next byte or go back into idle mode 
			R_CHUNKER_TRANSMITTING: begin
				if (is_tx_done == 1) begin
					if (!is_type_escape_sent) begin
						is_type_escape_sent <= 1;
						r_chunker_state <= R_CHUNKER_LOADING;
					end else if (!is_type_value_sent) begin
						is_type_value_sent <= 1;
						r_chunker_state <= R_CHUNKER_LOADING;
					end else if (active_chunk == 0 && r_did_we_escape_null_already == 0) begin
						// We just _escaped_ a null-byte, lets now send the actual null-byte value
						// i.e. lets not increment r_chunk_byte_index,
						// because we're only about to send the null-byte value
						r_did_we_escape_null_already <= 1;
						r_chunker_state <= R_CHUNKER_LOADING;
					end else if (r_chunk_byte_index == r_chunk_final_byte_index) begin
						// We're done, all chunk bytes written, start idling
						r_did_we_escape_null_already <= 0;
						r_chunker_state <= R_CHUNKER_IDLE;
						r_chunk_byte_index <= 0;
						is_type_escape_sent <= 0;
						is_type_value_sent <= 0;
					end else begin
						// More bytes to write in the chunk, keep loading and sending
						r_did_we_escape_null_already <= 0;
						r_chunk_byte_index <= r_chunk_byte_index + 1;
						r_chunker_state <= R_CHUNKER_LOADING;
					end
				end
			end
		endcase
	end

	// Outputs
	assign is_tx_ready = r_tx_ready;
	assign tx_data = r_tx_data;
endmodule
