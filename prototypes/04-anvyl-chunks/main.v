// Import NANDLAND's UART Verilog
include "uart_rx.v";
include "uart_tx.v";

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
	// Instantiate NANDLAND's UART RX instance
	wire [7:0] rx_data;
	reg [7:0] last_rx_data;
	wire rx_ready;

	uart_rx uart_rx_instance (
		.i_Clock(CLK),
		.i_Rx_Serial(T19),
		.o_Rx_DV(rx_ready),
		.o_Rx_Byte(rx_data)
	);
	
	// Print out state of received data on physical LEDs
	reg [0:7] r_ld = 0;
	assign LD0 = r_ld[0];
	assign LD1 = r_ld[1];
	assign LD2 = r_ld[2];
	assign LD3 = r_ld[3];
	assign LD4 = r_ld[4];
	assign LD5 = r_ld[5];
	assign LD6 = r_ld[6];
	assign LD7 = r_ld[7];

	// Copy the data when it's been read
	always @(posedge CLK)
	begin
		if (rx_ready == 1) begin
			last_rx_data <= rx_data;
		end
	end
	
	// Instantiate NANDLAND's UART TX instance
	reg r_tx_ready = 0;
	reg [7:0] tx_data = 0;
	wire tx_done;
	
	uart_tx uart_tx_instance (
		.i_Clock(CLK),
		.i_Tx_DV(r_tx_ready),
		.i_Tx_Byte(tx_data),
		.o_Tx_Active(),
		.o_Tx_Serial(T20),
		.o_Tx_Done(tx_done)
	);
	
	// Stuff
	wire [7:0] rx_data_reg_prim = last_rx_data + 1;
	wire [7:0] rx_data_reg_prim_2 = last_rx_data + 2;
	wire [7:0] rx_data_reg_prim_3 = last_rx_data + 3;

	// Buffer-based chunk sender
	parameter BUFFER_BYTE_SIZE = 3;
	reg [(BUFFER_BYTE_SIZE * 8) - 1:0] r_chunk = 0;
	parameter BUFFER_FILLED_BYTE_SIZE = 32;

	reg [BUFFER_FILLED_BYTE_SIZE - 1:0] r_chunk_filled_byte_count = 0;
	reg [BUFFER_FILLED_BYTE_SIZE - 1:0] r_last_chunk_filled_byte_count = 0;
	wire [BUFFER_FILLED_BYTE_SIZE - 1:0] r_chunk_final_byte_index;
	assign r_chunk_final_byte_index = r_last_chunk_filled_byte_count - 1;

	reg r_chunk_ready = 0;

	parameter CHUNK_BYTE_INDEX_SIZE = 32;
	reg [CHUNK_BYTE_INDEX_SIZE - 1:0] r_chunk_byte_index = 0;

	parameter R_CHUNKER_STATE_SIZE = 3;
	parameter R_CHUNKER_IDLE = 0;
	parameter R_CHUNKER_LOADING = 1;
	parameter R_CHUNKER_TRIGGERING = 2;
	parameter R_CHUNKER_TRIGGERED = 3;
	parameter R_CHUNKER_TRANSMITTING = 4;
	reg [R_CHUNKER_STATE_SIZE - 1:0] r_chunker_state = R_CHUNKER_IDLE;
	
	always @(posedge CLK) begin
		case (r_chunker_state)
			// While in idle mode - wait for the next chunk to be sent
			// if chunk is ready, switch into loading mode
			R_CHUNKER_IDLE: begin
				r_ld <= r_chunker_state;
				if (r_chunk_ready == 1) begin
					r_chunker_state <= R_CHUNKER_LOADING;
					r_ld <= r_last_chunk_filled_byte_count;
					r_last_chunk_filled_byte_count <= r_chunk_filled_byte_count;
				end
			end
			// Load the next byte from the chunk into the UART TX module
			R_CHUNKER_LOADING: begin
				tx_data[0] <= r_chunk[(r_chunk_byte_index * 8) + 0];
				tx_data[1] <= r_chunk[(r_chunk_byte_index * 8) + 1];
				tx_data[2] <= r_chunk[(r_chunk_byte_index * 8) + 2];
				tx_data[3] <= r_chunk[(r_chunk_byte_index * 8) + 3];
				tx_data[4] <= r_chunk[(r_chunk_byte_index * 8) + 4];
				tx_data[5] <= r_chunk[(r_chunk_byte_index * 8) + 5];
				tx_data[6] <= r_chunk[(r_chunk_byte_index * 8) + 6];
				tx_data[7] <= r_chunk[(r_chunk_byte_index * 8) + 7];
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
				if (tx_done == 1) begin
					if (r_chunk_byte_index == r_chunk_final_byte_index) begin
						// We're done, all chunk bytes written, start idling
						r_chunker_state <= R_CHUNKER_IDLE;
						r_chunk_byte_index <= 0;
					end else begin
						// More bytes to write in the chunk, keep loading and sending
						r_chunk_byte_index <= r_chunk_byte_index + 1;
						r_chunker_state <= R_CHUNKER_LOADING;
					end
				end
			end
		endcase
	end

	// Make a CLK-based sleep counter for printing stuff
	reg [31:0] r_ticks = 0;

	// Every N ticks print data and reset counter
	// 100000000 = 1 second
	// 100000000 = 1 second
	//  30000000 = 0.3 second
	//  10000000 = 0.1 second
	//   5000000 = 0.05 second
	//
	// Currently 0.05 seconds is the serial port refresh rate
	// although every read is 8 bytes, this program only writes 
	// 1 byte per the refresh rate i.e. you can go ~8 times faster
	// i.e. somewhere around 0.0625 seconds and thereby
	// the agent will read 8 bytes every 0.05 seconds
	//
	// N.B. If you write too fast, then the agent won't catch up
	// and eventually will lag extremely behind and you'll be sad
	// parameter sleep = 32'd200000000; // Around 0.5 FPS
	parameter sleep = 32'd100000000; // Around 1 FPS
	// parameter sleep = 32'd30000000; // Around 3 FPS
    // parameter sleep = 32'd2000000; // Around 50 FPS
	always @(posedge CLK)
	begin
		if (r_ticks < sleep) begin
			r_ticks = r_ticks + 1;
		end else if (r_ticks == sleep) begin
			r_chunk[0] <= rx_data_reg_prim[0];
			r_chunk[1] <= rx_data_reg_prim[1];
			r_chunk[2] <= rx_data_reg_prim[2];
			r_chunk[3] <= rx_data_reg_prim[3];
			r_chunk[4] <= rx_data_reg_prim[4];
			r_chunk[5] <= rx_data_reg_prim[5];
			r_chunk[6] <= rx_data_reg_prim[6];
			r_chunk[7] <= rx_data_reg_prim[7];

			r_chunk[8]  <= rx_data_reg_prim_2[0];
			r_chunk[9]  <= rx_data_reg_prim_2[1];
			r_chunk[10] <= rx_data_reg_prim_2[2];
			r_chunk[11] <= rx_data_reg_prim_2[3];
			r_chunk[12] <= rx_data_reg_prim_2[4];
			r_chunk[13] <= rx_data_reg_prim_2[5];
			r_chunk[14] <= rx_data_reg_prim_2[6];
			r_chunk[15] <= rx_data_reg_prim_2[7];

			r_chunk[16] <= rx_data_reg_prim_3[0];
			r_chunk[17] <= rx_data_reg_prim_3[1];
			r_chunk[18] <= rx_data_reg_prim_3[2];
			r_chunk[19] <= rx_data_reg_prim_3[3];
			r_chunk[20] <= rx_data_reg_prim_3[4];
			r_chunk[21] <= rx_data_reg_prim_3[5];
			r_chunk[22] <= rx_data_reg_prim_3[6];
			r_chunk[23] <= rx_data_reg_prim_3[7];

			r_chunk_ready <= 1;
			r_chunk_filled_byte_count <= 3;

			r_ticks = r_ticks + 1;
		end else if (r_ticks > sleep) begin
			r_chunk_ready <= 0;
			r_chunk_filled_byte_count <= 0;

			r_ticks = 0;
		end
	end
endmodule
