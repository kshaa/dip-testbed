// Import NANDLAND's UART RX
include "uart_rx.v";
// Import NANDLAND's UART TX
include "uart_tx.v";
// Import kshaa's typed & chunked UART TX
include "uart_tx_typed_chunker.v";

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
	wire rx_ready;

	uart_rx uart_rx_instance (
		.i_Clock(CLK),
		.i_Rx_Serial(T19),
		.o_Rx_DV(rx_ready),
		.o_Rx_Byte(rx_data)
	);

	// // Buffer-based chunk receiver
	// parameter RX_BUFFER_BYTE_SIZE = 5;
	// parameter RX_BUFFER_INDEX_SIZE = 32;
	
	// reg r_is_chunk_ready = 0;
	// reg [7:0] r_chunk_type = 0;
	// reg [BUFFER_INDEX_SIZE - 1:0] r_chunk_byte_size = 0;
	// reg [(BUFFER_BYTE_SIZE * 8) - 1:0] r_chunk_bytes = 0;
	
	// wire chunk_is_tx_ready;
	// wire [7:0] chunk_tx_data;
	
	// uart_rx_typed_chunker #(
	// 	.BUFFER_BYTE_SIZE(BUFFER_BYTE_SIZE),
	// 	.BUFFER_INDEX_SIZE(BUFFER_INDEX_SIZE)
	// ) uart_rx_typed_chunker_instance (
	// 	.CLK(CLK),
	// 	.is_chunk_ready(r_is_chunk_ready),
	// 	.chunk_byte_size(r_chunk_byte_size),
	// 	.is_tx_done(is_tx_done),
	// 	.chunk_bytes(r_chunk_bytes),
	// 	.chunk_type(r_chunk_type),
	// 	.is_tx_ready(chunk_is_tx_ready),
	// 	.tx_data(chunk_tx_data)
	// );

	// assign is_tx_ready = chunk_is_tx_ready;
	// assign tx_data = chunk_tx_data;

	// Instantiate NANDLAND's UART TX instance
	wire is_tx_ready;
	wire [7:0] tx_data;
	wire is_tx_done;

	uart_tx uart_tx_instance (
		.i_Clock(CLK),
		.i_Tx_DV(is_tx_ready),
		.i_Tx_Byte(tx_data),
		.o_Tx_Active(),
		.o_Tx_Serial(T20),
		.o_Tx_Done(is_tx_done)
	);

	// Buffer-based chunk sender
	parameter TX_BUFFER_BYTE_SIZE = 5;
	parameter TX_BUFFER_INDEX_SIZE = 32;
	
	reg r_is_chunk_ready = 0;
	reg [7:0] r_chunk_type = 0;
	reg [TX_BUFFER_INDEX_SIZE - 1:0] r_chunk_byte_size = 0;
	reg [(TX_BUFFER_BYTE_SIZE * 8) - 1:0] r_chunk_bytes = 0;
	
	wire chunk_is_tx_ready;
	wire [7:0] chunk_tx_data;
	
	uart_tx_typed_chunker #(
		.BUFFER_BYTE_SIZE(TX_BUFFER_BYTE_SIZE),
		.BUFFER_INDEX_SIZE(TX_BUFFER_INDEX_SIZE)
	) uart_tx_typed_chunker_instance (
		.CLK(CLK),
		.is_chunk_ready(r_is_chunk_ready),
		.chunk_byte_size(r_chunk_byte_size),
		.is_tx_done(is_tx_done),
		.chunk_bytes(r_chunk_bytes),
		.chunk_type(r_chunk_type),
		.is_tx_ready(chunk_is_tx_ready),
		.tx_data(chunk_tx_data)
	);

	assign is_tx_ready = chunk_is_tx_ready;
	assign tx_data = chunk_tx_data;

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
	reg [7:0] last_rx_data;
	always @(posedge CLK)
	begin
		if (rx_ready == 1) begin
			r_ld <= rx_data;
			last_rx_data <= rx_data;
		end
	end
	
	// Create bytes for input with several increments
	wire [7:0] rx_data_reg_prim = last_rx_data + 1;
	wire [7:0] rx_data_reg_prim_2 = last_rx_data + 2;
	wire [7:0] rx_data_reg_prim_3 = last_rx_data + 3;

	// Every N ticks print data and reset counter
	// 100000000 = 1 second 	/ 1 FPS
	//  30000000 = 0.3 second 	/ 3 FPS
	//  10000000 = 0.1 second	/ 10 FPS
	//   5000000 = 0.05 second	/ 20 FPS
	//   2000000 = 0.02 second	/ 50 FPS
	parameter sleep = 32'd100000000;

	// An FSM based on CLK, which sends some data every N ticks
	reg [31:0] r_ticks = 0;
	always @(posedge CLK)
	begin
		if (r_ticks < sleep) begin
			// Tick clock
			r_ticks = r_ticks + 1;
		end else if (r_ticks == sleep) begin
			// Tick clock
			r_ticks = r_ticks + 1;

			// Load data type into chunker
			// [0x00] [0x00] is reserved for an escaped null-byte
			// [0x00] [0x01] is reserved for an escaped end of chunk
			// [0x00] [0x02++] is available for types 
			r_chunk_type <= 2;

			// Load some random data into chunk
			r_chunk_bytes[7:0] <= rx_data_reg_prim;
			r_chunk_bytes[15:8] <= rx_data_reg_prim_2;
			r_chunk_bytes[23:16] <= rx_data_reg_prim_3;
			r_chunk_bytes[31:24] <= 0;
			r_chunk_bytes[39:32] <= rx_data_reg_prim_3;

			// The serial port result for this is:
			// [0x0] [0x2] 	-- escaped chunk type
			// [0x1] 		-- rx_data_reg_prim
			// [0x2] 		-- rx_data_reg_prim_2
			// [0x3] 		-- rx_data_reg_prim_3
			// [0x0] [0x0]	-- escaped null byte
			// [0x3] 		-- rx_data_reg_prim_3
			// [0x0] [0x1]	-- escaped end of chunk

			// Turn on chunked TX
			r_is_chunk_ready <= 1;
			r_chunk_byte_size <= 5;
		end else if (r_ticks > sleep) begin
			// Reset clock
			r_ticks = 0;

			// Turn off chunked TX
			r_is_chunk_ready <= 0;
			r_chunk_byte_size <= 0;
		end
	end
endmodule
