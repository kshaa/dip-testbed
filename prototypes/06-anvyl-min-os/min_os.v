// Import NANDLAND's UART RX
`include "uart_rx.v"
// Import NANDLAND's UART TX
`include "uart_tx.v"
// Import kshaa's typed & chunked UART TX
`include "uart_tx_typed_chunker.v"
// Import kshaa's typed & chunked UART RX
`include "uart_rx_typed_chunker.v"
// Import kshaa's virtual interface "leds"
`include "v_leds.v"
// Import kshaa's virtual interface "switches"
`include "v_switches.v"

// Define kshaa's MinOS module that abstracts over UART and exposes some virtual interfaces
module min_os(
	// Clock pin
	input CLK,
	
	// UART RX/TX pins
	input T19,
	output T20,

	// Virtual interface "leds"
	input [7:0] leds,

	// Virtual interface "switches"
	output [7:0] switches
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

	// Instantiate kshaa's buffer-based chunk receiver
	parameter RX_CONTENT_BUFFER_BYTE_SIZE = 3;
	parameter RX_CONTENT_BUFFER_INDEX_SIZE = 32;

	wire [7:0] rx_chunk_type;
	wire [(RX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:0] rx_chunk_bytes;
	wire [RX_CONTENT_BUFFER_INDEX_SIZE - 1:0] rx_chunk_byte_size;
	wire rx_is_chunk_ready;
	uart_rx_typed_chunker #(
		.CONTENT_BUFFER_BYTE_SIZE(RX_CONTENT_BUFFER_BYTE_SIZE),
		.CONTENT_BUFFER_INDEX_SIZE(RX_CONTENT_BUFFER_INDEX_SIZE)
	) uart_rx_typed_chunker_instance (
		.CLK(CLK),
		.rx_data(rx_data),
		.is_rx_ready(rx_ready),
		.chunk_type(rx_chunk_type),
		.chunk_bytes(rx_chunk_bytes),
		.chunk_byte_size(rx_chunk_byte_size),
		.is_chunk_ready(rx_is_chunk_ready)
	);

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

	// Instantiate kshaa's buffer-based chunk sender
	parameter TX_CONTENT_BUFFER_BYTE_SIZE = 5;
	parameter TX_CONTENT_BUFFER_INDEX_SIZE = 32;
	
	reg r_tx_is_chunk_ready = 0;
	reg [7:0] r_tx_chunk_type = 0;
	reg [TX_CONTENT_BUFFER_INDEX_SIZE - 1:0] r_tx_chunk_byte_size = 0;
	reg [(TX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:0] r_tx_chunk_bytes = 0;
	
	wire chunk_is_tx_ready;
	wire [7:0] chunk_tx_data;
	wire is_tx_chunker_done;
	
	uart_tx_typed_chunker #(
		.CONTENT_BUFFER_BYTE_SIZE(TX_CONTENT_BUFFER_BYTE_SIZE),
		.CONTENT_BUFFER_INDEX_SIZE(TX_CONTENT_BUFFER_INDEX_SIZE)
	) uart_tx_typed_chunker_instance (
		.CLK(CLK),
		.is_chunk_ready(r_tx_is_chunk_ready),
		.chunk_byte_size(r_tx_chunk_byte_size),
		.is_tx_done(is_tx_done),
		.chunk_bytes(r_tx_chunk_bytes),
		.chunk_type(r_tx_chunk_type),
		.is_tx_ready(chunk_is_tx_ready),
		.tx_data(chunk_tx_data),
		.is_chunker_done(is_tx_chunker_done)
	);

	assign is_tx_ready = chunk_is_tx_ready;
	assign tx_data = chunk_tx_data;

	// Instantiate virtual interface "leds"
	parameter LEDS_INTERFACE_TX_CHUNK_TYPE = 2;

	reg r_leds_reset = 0;
	
	wire leds_should_update;
	wire [7:0] leds_tx_chunk_type;
	wire [7:0] leds_tx_chunk_bytes;

	v_leds #(
		.INTERFACE_TX_CHUNK_TYPE(LEDS_INTERFACE_TX_CHUNK_TYPE)
	) v_leds_instance (
		.CLK(CLK),
		.leds(leds),
		.should_update(leds_should_update),
		.tx_chunk_type(leds_tx_chunk_type),
		.tx_chunk_bytes(leds_tx_chunk_bytes),
		.reset(r_leds_reset)
	);

	// Instantiate virtual interface "switches"
	parameter SWITCHES_INTERFACE_RX_CHUNK_TYPE = 4;
	v_switches #(
		.INTERFACE_RX_CHUNK_TYPE(SWITCHES_INTERFACE_RX_CHUNK_TYPE),
		.RX_CONTENT_BUFFER_BYTE_SIZE(RX_CONTENT_BUFFER_BYTE_SIZE),
		.RX_CONTENT_BUFFER_INDEX_SIZE(RX_CONTENT_BUFFER_INDEX_SIZE)
	) v_switches_instance (
		.CLK(CLK),
		.rx_chunk_type(rx_chunk_type),
		.rx_chunk_bytes(rx_chunk_bytes),
		.rx_chunk_byte_size(rx_chunk_byte_size),
		.rx_is_chunk_ready(rx_is_chunk_ready),
		.switches(switches)
	);

	// An FSM "MinOS" which schedules sending out virtual interface data over the serial interface
	parameter R_MINOS_STATE_SIZE = 3;
	parameter R_MINOS_IDLE = 0;
	parameter R_MINOS_LEDS_START_WRITING = 1;
	parameter R_MINOS_LEDS_STOP_WRITING = 2;
	parameter R_MINOS_LEDS_WAIT_TRANSMISSION = 3;
	parameter R_MINOS_FINISHED = 4;
	reg [R_MINOS_STATE_SIZE - 1:0] r_minos_state = R_MINOS_IDLE;
 
	always @(posedge CLK)
	begin
		case (r_minos_state)
			R_MINOS_IDLE: begin
				if (leds_should_update) begin
					r_minos_state <= R_MINOS_LEDS_START_WRITING;
				end
			end

			R_MINOS_LEDS_START_WRITING: begin
				// Load received chunk type into transmitted chunk type
				r_tx_chunk_type <= leds_tx_chunk_type;

				// Load received chunk data into transmitted chunk data
				r_tx_chunk_bytes[7:0] <= leds_tx_chunk_bytes;

				// Trigger chunked TX
				r_tx_is_chunk_ready <= 1;
				r_tx_chunk_byte_size <= 1;

				// Inform virtual interface that the update has happened
				r_leds_reset <= 1;

				// Stop sending data to chunker and wait for the transmission to finish
				r_minos_state <= R_MINOS_LEDS_STOP_WRITING;
			end
			R_MINOS_LEDS_STOP_WRITING: begin
				r_tx_is_chunk_ready <= 0;
				r_tx_chunk_byte_size <= 0;
				r_leds_reset <= 0;
				r_minos_state <= R_MINOS_LEDS_WAIT_TRANSMISSION;
			end
			R_MINOS_LEDS_WAIT_TRANSMISSION: begin
				if (is_tx_chunker_done) begin
					r_minos_state <= R_MINOS_FINISHED;
				end
			end

			R_MINOS_FINISHED: begin
				r_minos_state <= R_MINOS_IDLE;
			end
		endcase
	end
endmodule
