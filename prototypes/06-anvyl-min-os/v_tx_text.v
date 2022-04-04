module v_tx_text #(
	parameter [7:0] INTERFACE_TX_CHUNK_TYPE = 5,
	// The size of the display in bytes
	parameter TEXT_BUFFER_BYTE_SIZE = 33,
	// How many bits needed to index the whole buffer
	parameter TEXT_BUFFER_INDEX_SIZE = 8
)(
	// clock pin
	input CLK,

	// active text state
	input [((TEXT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] text_bytes,
	input [(TEXT_BUFFER_INDEX_SIZE -1):0] text_size,
	
	// signal to inform the user of this module that text
	// has changed its value and should be updated i.e. sent out over UART 
	output should_update,

	// the value that the text has been updated to
	output [7:0] tx_chunk_type,
	output [(TEXT_BUFFER_INDEX_SIZE - 1):0] tx_chunk_size,
	output [((TEXT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] tx_chunk_bytes,

	// signal to tell this module "the text has been updated, chill out"
	input reset
);
	// The TX chunk type
	reg [7:0] r_tx_chunk_type = INTERFACE_TX_CHUNK_TYPE;
	// What's the last updated value of text
	reg [((TEXT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] r_last_text_bytes = 0;
	reg [(TEXT_BUFFER_INDEX_SIZE - 1):0] r_last_text_size = 0;

	// An FSM to receive leds and send them out over UART when they're changed
	parameter R_VTEXT_STATE_SIZE = 3;
	parameter R_VTEXT_IDLE = 0;
	parameter R_VTEXT_SHOULD_PREPARE = 1;
	parameter R_VTEXT_SHOULD_UPDATE = 2;
	parameter R_VTEXT_FINISH = 3;
	reg [R_VTEXT_STATE_SIZE - 1:0] r_vtext_state = R_VTEXT_IDLE;
 
 	integer buffer_iterator = 0;
	always @(posedge CLK)
	begin
		case (r_vtext_state)
			R_VTEXT_IDLE: begin
				if (text_bytes != r_last_text_bytes) begin
					r_last_text_bytes <= text_bytes;
					r_last_text_size <= text_size;
					r_vtext_state <= R_VTEXT_SHOULD_PREPARE;
				end
			end
			R_VTEXT_SHOULD_PREPARE: begin
				r_vtext_state <= R_VTEXT_SHOULD_UPDATE;
			end
			R_VTEXT_SHOULD_UPDATE: begin
				if (reset) begin
					r_vtext_state <= R_VTEXT_FINISH;
				end
			end
			R_VTEXT_FINISH: begin
				r_vtext_state <= R_VTEXT_IDLE;
			end
		endcase
	end

	// Outputs
	assign should_update = r_vtext_state == R_VTEXT_SHOULD_UPDATE;
	assign tx_chunk_type = r_tx_chunk_type;
	assign tx_chunk_size = r_last_text_size;
	assign tx_chunk_bytes = r_last_text_bytes;
endmodule
