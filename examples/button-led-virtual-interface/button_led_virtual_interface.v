// Import NANDLAND's UART Verilog
`include "uart_rx.v"
`include "uart_tx.v"

// Define a UART reader/transmitter FPGA program
module button_led_virtual_interface #(
	// Send state over serial only on changes
	parameter SEND_ON_CHANGE = 0,
	// How many clock ticks for receiving a bit
	// (see `uart_rx.v` or `uart_tx.v` for more comments)
	parameter CLKS_PER_BIT = 868,
	// How many clock ticks until state is checked and possibly transmitted/synchronized
	parameter CLKS_PER_SYNC = 32'd1666666
)(
	// Clock pin
	input CLK,
	
	// UART RX/TX pins
	input T19,
	output T20,

	// LED interface
	input [7:0] leds,

	// Button interface
	output [23:0] buttons,

	// State synchronization
	// (each bit is raised for one clock cycle)
	output tx_in_progress,
	output tx_is_done,
	output rx_is_done
);
	// Instantiate NANDLAND's UART RX instance
	reg [7:0] r_rx_data = 8'b00000000;
	reg r_rx_is_done = 0;
	assign rx_is_done = r_rx_is_done;
	wire rx_is_done_internal;
	wire [7:0] rx_data;
	uart_rx #(
		.CLKS_PER_BIT(CLKS_PER_BIT)
	) uart_rx_instance (
		.i_Clock(CLK),
		.i_Rx_Serial(T19),
		.o_Rx_DV(rx_is_done_internal),
		.o_Rx_Byte(rx_data)
	);

	// Copy the data when it's been read
	always @(posedge CLK)
	begin
		if (rx_is_done_internal == 1) begin
			r_rx_data = rx_data;
			r_rx_is_done = 1;
		end else if (rx_is_done_internal == 0 && r_rx_is_done == 1) begin
			// After one clock cycle, turn off rx_is_done
			r_rx_is_done = 0;
		end
	end

	// Assign received data to buttons
	assign buttons[0] = r_rx_is_done && r_rx_data == 0;
	assign buttons[1] = r_rx_is_done && r_rx_data == 1;
	assign buttons[2] = r_rx_is_done && r_rx_data == 2;
	assign buttons[3] = r_rx_is_done && r_rx_data == 3;
	assign buttons[4] = r_rx_is_done && r_rx_data == 4;
	assign buttons[5] = r_rx_is_done && r_rx_data == 5;
	assign buttons[6] = r_rx_is_done && r_rx_data == 6;
	assign buttons[7] = r_rx_is_done && r_rx_data == 7;
	assign buttons[8] = r_rx_is_done && r_rx_data == 8;
	assign buttons[9] = r_rx_is_done && r_rx_data == 9;
	assign buttons[10] = r_rx_is_done && r_rx_data == 10;
	assign buttons[11] = r_rx_is_done && r_rx_data == 11;
	assign buttons[12] = r_rx_is_done && r_rx_data == 12;
	assign buttons[13] = r_rx_is_done && r_rx_data == 13;
	assign buttons[14] = r_rx_is_done && r_rx_data == 14;
	assign buttons[15] = r_rx_is_done && r_rx_data == 15;
	assign buttons[16] = r_rx_is_done && r_rx_data == 16;
	assign buttons[17] = r_rx_is_done && r_rx_data == 17;
	assign buttons[18] = r_rx_is_done && r_rx_data == 18;
	assign buttons[19] = r_rx_is_done && r_rx_data == 19;
	assign buttons[20] = r_rx_is_done && r_rx_data == 20;
	assign buttons[21] = r_rx_is_done && r_rx_data == 21;
	assign buttons[22] = r_rx_is_done && r_rx_data == 22;
	assign buttons[23] = r_rx_is_done && r_rx_data == 23;
	
	// Instantiate NANDLAND's UART TX instance
	reg [7:0] r_old_led_state = 0;
	reg r_just_started = 1;
	reg r_tx_in_progress = 0;
	assign tx_in_progress = r_tx_in_progress;
	reg r_tx_enable = 0;
	uart_tx #(
		.CLKS_PER_BIT(CLKS_PER_BIT)
	) uart_tx_instance (
		.i_Clock(CLK),
		.i_Tx_DV(r_tx_enable),
		// LED's are the bits to-be-transmitted
		.i_Tx_Byte(leds),
		.o_Tx_Active(),
		.o_Tx_Serial(T20),
		.o_Tx_Done(tx_is_done)
	);

	// Clock tick counter for state synchronization timing
	reg [31:0] r_ticks = 0;

	// Regularly (every CLKS_PER_SYNC) check LED state and transmit on changes 
	always @(posedge CLK)
	begin
		// Keep ticking clock until next sync
		if (r_ticks < CLKS_PER_SYNC) begin
			r_ticks = r_ticks + 1;
		end
		// When sleep counter reached, execute sync
		else if (r_ticks == CLKS_PER_SYNC) begin
			// Execute sync only when first started and when bits changed
			if ((SEND_ON_CHANGE == 0) || ((leds != r_old_led_state) || r_just_started == 1)) begin
				r_tx_in_progress = 1;
				r_old_led_state = leds;
				r_just_started = 0;
				r_tx_enable = 1;
			end
			// Keep ticking
			r_ticks = r_ticks + 1;
		end else begin
			// After sync, update outputs, stop transmisison & reset clock
			r_tx_in_progress = 0;
			r_tx_enable = 0;
			r_ticks = 0;
		end
	end
endmodule
