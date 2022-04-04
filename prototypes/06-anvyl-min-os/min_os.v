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
// Import kshaa's virtual interface "display"
`include "v_display.v"
// Import kshaa's virtual interface "buttons"
`include "v_buttons.v"
// Import kshaa's virtual interface "rx_text"
`include "v_rx_text.v"
// Import kshaa's virtual interface "tx_text"
`include "v_tx_text.v"

// Define kshaa's MinOS module that abstracts over UART and exposes some virtual interfaces
module min_os(
	// Clock pin
	input CLK,
	
	// UART RX/TX pins
	input T19,
	output T20,

	// Virtual interface "leds"
	input [7:0] leds,

	// Virtual interface "display"
	input [511:0] display, // 64 bytes

	// Virtual interface "switches"
	output [7:0] switches,

	// Virtual interface "buttons"
	output [7:0] button_index,
	output button_pressed,

	// Virtual interface "rx_text"
	output [(32 * 8) - 1:0] rx_text_bytes,
	output [7:0] rx_text_size,
	output rx_is_text_ready,

	// Virtual interface "tx_text"
	input [(32 * 8) - 1:0] tx_text_bytes,
	input [7:0] tx_text_size
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
	parameter RX_CONTENT_BUFFER_BYTE_SIZE = 33;
	parameter RX_CONTENT_BUFFER_INDEX_SIZE = 8;

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
	parameter TX_CONTENT_BUFFER_BYTE_SIZE = 33;
	parameter TX_CONTENT_BUFFER_INDEX_SIZE = 8;
	
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

	// Instantiate virtual interface "display"
	parameter DISPLAY_INTERFACE_TX_CHUNK_TYPE = 6;
	parameter DISPLAY_BUFFER_BYTE_SIZE = 64;
	parameter DISPLAY_BUFFER_INDEX_SIZE = 32;

	reg r_display_reset = 0;
	
	wire display_should_update;
	wire [7:0] display_tx_chunk_type;
	wire [15:0] display_tx_chunk_bytes;

	v_display #(
		.INTERFACE_TX_CHUNK_TYPE(DISPLAY_INTERFACE_TX_CHUNK_TYPE),
		.DISPLAY_BUFFER_BYTE_SIZE(DISPLAY_BUFFER_BYTE_SIZE),
		.DISPLAY_BUFFER_INDEX_SIZE(DISPLAY_BUFFER_INDEX_SIZE)
	) v_display_instance (
		.CLK(CLK),
		.display(display),
		.should_update(display_should_update),
		.tx_chunk_type(display_tx_chunk_type),
		.tx_chunk_bytes(display_tx_chunk_bytes),
		.reset(r_display_reset)
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

	// Instantiate virtual interface "buttons"
	parameter BUTTONS_INTERFACE_RX_CHUNK_TYPE = 3;
	v_buttons #(
		.INTERFACE_RX_CHUNK_TYPE(BUTTONS_INTERFACE_RX_CHUNK_TYPE),
		.RX_CONTENT_BUFFER_BYTE_SIZE(RX_CONTENT_BUFFER_BYTE_SIZE),
		.RX_CONTENT_BUFFER_INDEX_SIZE(RX_CONTENT_BUFFER_INDEX_SIZE)
	) v_buttons_instance (
		.CLK(CLK),
		.rx_chunk_type(rx_chunk_type),
		.rx_chunk_bytes(rx_chunk_bytes),
		.rx_chunk_byte_size(rx_chunk_byte_size),
		.rx_is_chunk_ready(rx_is_chunk_ready),
		.button_index(button_index),
		.button_pressed(button_pressed)
	);

	// Instantiate virtual interface "rx_text"
	parameter RX_TEXT_INTERFACE_RX_CHUNK_TYPE = 5;
	v_rx_text #(
		.INTERFACE_RX_CHUNK_TYPE(RX_TEXT_INTERFACE_RX_CHUNK_TYPE),
		.RX_CONTENT_BUFFER_BYTE_SIZE(RX_CONTENT_BUFFER_BYTE_SIZE),
		.RX_CONTENT_BUFFER_INDEX_SIZE(RX_CONTENT_BUFFER_INDEX_SIZE)
	) v_rx_text_instance (
		.CLK(CLK),
		.rx_chunk_type(rx_chunk_type),
		.rx_chunk_bytes(rx_chunk_bytes),
		.rx_chunk_byte_size(rx_chunk_byte_size),
		.rx_is_chunk_ready(rx_is_chunk_ready),
		.rx_text_bytes(rx_text_bytes),
		.rx_text_size(rx_text_size),
		.rx_is_text_ready(rx_is_text_ready)
	);

	// Instantiate virtual interface "tx_text"
	parameter TX_TEXT_INTERFACE_TX_CHUNK_TYPE = 5;
	reg r_text_reset = 0;
	wire text_should_update;
	wire [7:0] text_tx_chunk_type;
	wire [7:0] text_tx_chunk_size;
	wire [((TX_CONTENT_BUFFER_BYTE_SIZE - 1) * 8) - 1:0] text_tx_chunk_bytes;
	v_tx_text #(
		.INTERFACE_TX_CHUNK_TYPE(TX_TEXT_INTERFACE_TX_CHUNK_TYPE),
		.TEXT_BUFFER_BYTE_SIZE(TX_CONTENT_BUFFER_BYTE_SIZE),
		.TEXT_BUFFER_INDEX_SIZE(TX_CONTENT_BUFFER_INDEX_SIZE)
	) v_tx_text_instance (
		.CLK(CLK),
		.text_bytes(tx_text_bytes),
		.text_size(tx_text_size),
		.should_update(text_should_update),
		.tx_chunk_type(text_tx_chunk_type),
		.tx_chunk_size(text_tx_chunk_size),
		.tx_chunk_bytes(text_tx_chunk_bytes),
		.reset(r_text_reset)
	);

	// An FSM "MinOS" which schedules sending out virtual interface data over the serial interface
	parameter R_MINOS_STATE_SIZE = 4;
	parameter R_MINOS_IDLE = 0;
	
	parameter R_MINOS_LEDS_CHECK = 1;
	parameter R_MINOS_LEDS_START_WRITING = 2;
	parameter R_MINOS_LEDS_STOP_WRITING = 3;
	parameter R_MINOS_LEDS_WAIT_TRANSMISSION = 4;
	
	parameter R_MINOS_DISPLAY_CHECK = 5;
	parameter R_MINOS_DISPLAY_START_WRITING = 6;
	parameter R_MINOS_DISPLAY_STOP_WRITING = 7;
	parameter R_MINOS_DISPLAY_WAIT_TRANSMISSION = 8;

	parameter R_MINOS_TEXT_CHECK = 9;
	parameter R_MINOS_TEXT_START_WRITING = 10;
	parameter R_MINOS_TEXT_STOP_WRITING = 11;
	parameter R_MINOS_TEXT_WAIT_TRANSMISSION = 12;
	
	parameter R_MINOS_FINISHED = 13;

	reg [R_MINOS_STATE_SIZE - 1:0] r_minos_state = R_MINOS_IDLE;
 
  	integer buffer_iterator = 0;

	always @(posedge CLK)
	begin
		case (r_minos_state)
			R_MINOS_IDLE: begin
				if (leds_should_update || display_should_update || text_should_update) begin
					r_minos_state <= R_MINOS_LEDS_CHECK;
				end
			end

			R_MINOS_LEDS_CHECK: begin
				if (leds_should_update) begin
					r_minos_state <= R_MINOS_LEDS_START_WRITING;
				end else begin
					r_minos_state <= R_MINOS_DISPLAY_CHECK;
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
					r_minos_state <= R_MINOS_DISPLAY_CHECK;
				end
			end

			R_MINOS_DISPLAY_CHECK: begin
				if (display_should_update) begin
					r_minos_state <= R_MINOS_DISPLAY_START_WRITING;
				end else begin
					r_minos_state <= R_MINOS_FINISHED;
				end
			end
			R_MINOS_DISPLAY_START_WRITING: begin
				// Load received chunk type into transmitted chunk type
				r_tx_chunk_type <= display_tx_chunk_type;

				// Load received chunk data into transmitted chunk data
				r_tx_chunk_bytes[15:0] <= display_tx_chunk_bytes;

				// Trigger chunked TX
				r_tx_is_chunk_ready <= 1;
				r_tx_chunk_byte_size <= 2;

				// Inform virtual interface that the update has happened
				r_display_reset <= 1;

				// Stop sending data to chunker and wait for the transmission to finish
				r_minos_state <= R_MINOS_DISPLAY_STOP_WRITING;
			end
			R_MINOS_DISPLAY_STOP_WRITING: begin
				r_tx_is_chunk_ready <= 0;
				r_tx_chunk_byte_size <= 0;
				r_display_reset <= 0;
				r_minos_state <= R_MINOS_DISPLAY_WAIT_TRANSMISSION;
			end
			R_MINOS_DISPLAY_WAIT_TRANSMISSION: begin
				if (is_tx_chunker_done) begin
					r_minos_state <= R_MINOS_TEXT_CHECK;
				end
			end

			R_MINOS_TEXT_CHECK: begin
				if (text_should_update) begin
					r_minos_state <= R_MINOS_TEXT_START_WRITING;
				end else begin
					r_minos_state <= R_MINOS_FINISHED;
				end
			end
			R_MINOS_TEXT_START_WRITING: begin
				// Load received chunk type into transmitted chunk type
				r_tx_chunk_type <= text_tx_chunk_type;

				// Load received chunk data into transmitted chunk data
				r_tx_chunk_bytes[7:0] <= text_tx_chunk_size;
				r_tx_chunk_bytes[(TX_CONTENT_BUFFER_BYTE_SIZE * 8) - 1:8] <= text_tx_chunk_bytes;

				// Trigger chunked TX
				r_tx_is_chunk_ready <= 1;
				r_tx_chunk_byte_size <= 1 + text_tx_chunk_size;

				// Inform virtual interface that the update has happened
				r_text_reset <= 1;

				// Stop sending data to chunker and wait for the transmission to finish
				r_minos_state <= R_MINOS_TEXT_STOP_WRITING;
			end
			R_MINOS_TEXT_STOP_WRITING: begin
				r_tx_is_chunk_ready <= 0;
				r_tx_chunk_byte_size <= 0;
				r_text_reset <= 0;
				r_minos_state <= R_MINOS_TEXT_WAIT_TRANSMISSION;
			end
			R_MINOS_TEXT_WAIT_TRANSMISSION: begin
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
