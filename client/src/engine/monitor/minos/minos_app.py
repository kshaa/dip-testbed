"""Module for functionality related to serial socket monitor as button/led byte stream, specifically graphics/UI"""
import asyncio
from functools import partial
from typing import Optional, Any
from result import Err
from textual import events
from textual.app import App
from textual.views import GridView
from textual.widgets import Button
from src.domain.minos_chunks import LEDChunk, TextChunk
from src.domain.minos_monitor_event import GoodChunkReceived, TextChanged, ModeSwitched, SwitchesChanged, \
    IndexButtonClicked
from src.domain.monitor_message import AddTUISideEffect, ButtonPress
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.util import log

LOGGER = log.timed_named_logger("monitor_button_led_bytes_app")


class AppStateStorage:
    engine_state: Optional[EngineMonitorMinOSState] = None

    def update(self, engine_state: EngineMonitorMinOSState):
        self.engine_state = engine_state

    def message(self, message: Any):
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.engine_state.base.incoming_message_queue.put(message))


hacked_global_app_state_storage = AppStateStorage()

# Buttons
switch_keys = [
    "1", "2", "3", "4", "5", "6", "7", "8",
]
button_keys = [
    "q", "w", "e", "r", "t", "y", "u", "i",
    "a", "s", "d", "f", "g", "h", "j", "k",
    "z", "x", "c", "v", "b", "n", "m", ",",
]


class ButtonLEDScreen(GridView):
    """Screen for interacting with LEDs and buttons"""

    # Colors (https://www.ditig.com/256-colors-cheat-sheet)
    DARKER = "white on rgb(51,51,51)"
    DARK = "white on rgb(69,69,69)"
    LIGHT = "black on rgb(108,108,108)"
    LIGHTER = "black on rgb(168,168,168)"
    RED = "white on rgb(215,0,0)"

    def on_mount(self, event: events.Mount) -> None:
        """Event when widget is first mounted (added to a parent view)."""
        # Make all the pixels
        self.pixels = [
            Button(f"P{i} | off", style=self.DARKER, name=f"P{i}")
            for i in range(0, 8 * 8)
        ]

        # Make all the LEDs
        self.leds = [
            Button(f"L{7 - i} | off", style=self.DARK, name=f"L{7 - i}")
            for i in range(0, 8)
        ]

        # Make all the switches
        self.switches = [
            Button(f"S{7 - i} | {k}\noff", style=self.DARK, name=f"S{7 - i} | {k}\noff")
            for i, k in enumerate(switch_keys)
        ]

        # Make all the buttons
        self.buttons = [
            Button(f"B{i} | {k}", style=self.LIGHTER, name=f"B{i} | {k}")
            for (i, k) in enumerate(button_keys)
        ]

        # Make input text
        input = ""
        self.input_text = Button(f"Input: {input}", style=self.DARK, name="input_text")

        # Make output text
        output = ""
        self.output_text = Button(f"Output <inactive>: {output}", style=self.DARK, name="output_text")

        # Make stats
        self.stats = Button("(′ꈍωꈍ‵)", style=self.DARK, name=f"stats")

        # Make info
        info = "Information about the UI:\n" \
               "  P{N} - Display pixels, L{N} - LED panel,\n" \
               "  S{N} - Switch panel, B{N} - Button panel\n\n"
        self.info = Button(info, style=self.DARK, name=f"info")

        # Make controls
        controls = "Controls: \n" \
               "  [TAB] - Switch from text input to button-switch input\n" \
               "  [1 - 8] - Toggle switch value in button-switch mode\n" \
               "  [q - ,] - Send button signal in button-switch mode\n" \
               "  <text> & [ENTER] - Fill and send text field in text mode\n" \
               "  [ESC] - Exit this TUI"
        self.controls = Button(controls, style=self.DARK, name=f"controls")

        # Set basic grid settings
        self.grid.set_gap(2, 1)
        self.grid.set_gutter(1)
        self.grid.set_align("center", "center")

        # Create rows / columns / areas
        self.grid.add_column(fraction=5, name="maincol", repeat=8)
        self.grid.add_column(fraction=4, name="sidecol", repeat=8)
        self.grid.add_row(name="mainrow", repeat=8)
        self.grid.add_row(name="statsrow", repeat=1)
        areas = {
            "input": "sidecol1-start|sidecol8-end,mainrow6-start|mainrow6-end",
            "output": "sidecol1-start|sidecol8-end,mainrow7-start|mainrow7-end",
            "stats": "maincol1-start|maincol6-end,statsrow",
            "info": "maincol7-start|sidecol3-end,statsrow",
            "controls": "sidecol4-start|sidecol8-end,statsrow",
        }
        for i in range(0, 8 * 8):
            x = i % 8
            y = int(i / 8)
            area = f"p{i}"
            areas[area] = f"maincol{x + 1}-start|maincol{x + 1}-end,mainrow{y + 1}-start|mainrow{y + 1}-end"
        for i in range(0, 8):
            x = i % 8
            area = f"l{i}"
            areas[area] = f"sidecol{x + 1}-start|sidecol{x + 1}-end,mainrow1-start|mainrow1-end"

        for i in range(0, 8):
            x = i % 8
            area = f"s{i}"
            areas[area] = f"sidecol{x + 1}-start|sidecol{x + 1}-end,mainrow2-start|mainrow2-end"
        for i in range(0, 8 * 3):
            x = i % 8
            y = int(i / 8)
            area = f"b{i}"
            areas[area] = f"sidecol{x + 1}-start|sidecol{x + 1}-end,mainrow{y+3}-start|mainrow{y+3}-end"
        self.grid.add_areas(**areas)


        # Place out widgets in to the layout
        for i, pixel in enumerate(self.pixels):
            self.grid.add_widget(pixel, f"p{i}")
        for i, led in enumerate(self.leds):
            self.grid.add_widget(led, f"l{i}")
        for i, switch in enumerate(self.switches):
            self.grid.add_widget(switch, f"s{i}")
        for i, button in enumerate(self.buttons):
            self.grid.add_widget(button, f"b{i}")
        self.grid.place(input=self.input_text)
        self.grid.place(output=self.output_text)
        self.grid.place(stats=self.stats)
        self.grid.place(info=self.info)
        self.grid.place(controls=self.controls)

        # LED effect
        def on_led_change(led_index: int, led_on: bool):
            if 0 <= led_index < len(self.leds):
                self.leds[led_index].button_style = self.RED if led_on else self.DARK
                i = str(7 - led_index)
                s = "on" if led_on else "off"
                self.leds[led_index].label = f"L{i} | {s}"

        def expect_led_change(state: Any, event: Any):
            if not isinstance(event, GoodChunkReceived): return
            if not isinstance(event.parsed_chunk, LEDChunk): return
            fancy_byte = event.parsed_chunk.fancy_byte
            bits = fancy_byte.to_binary_bits()
            for index, is_on in enumerate(bits):
                on_led_change(index, is_on)
        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_led_change)))

        # Text out effect
        def expect_text_out_change(state: Any, event: Any):
            if isinstance(event, ModeSwitched):
                text = state.text_out
                state = "active" if event.is_text_mode else "inactive"
                self.output_text.label = f"Output <{state}>: {text}"
            if isinstance(event, TextChanged):
                text = event.text
                state = "active" if state.is_text_mode else "inactive"
                self.output_text.label = f"Output <{state}>: {text}"
        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_text_out_change)))

        # Button effect
        def expect_button_press(state: Any, event: Any):
            if isinstance(event, IndexButtonClicked):
                i = event.button_index
                k = button_keys[i]
                self.buttons[i].button_style = self.LIGHT
                self.buttons[i].label = f"B{i} | ."
                async def toggle_back():
                    await asyncio.sleep(0.2)
                    self.buttons[i].button_style = self.LIGHTER
                    self.buttons[i].label = f"B{i} | {k}"
                asyncio.create_task(toggle_back())
        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_button_press)))

        # Switch effect
        def on_switch_change(switch_index: int, switch_on: bool):
            if 0 <= switch_index < len(self.switches):
                self.switches[switch_index].button_style = self.RED if switch_on else self.DARK
                state = "on" if switch_on else "off"
                self.switches[switch_index].label = f"S{7 - switch_index} | {switch_index + 1}\n{state}"

        def expect_switch_change(state: Any, event: Any):
            if not isinstance(event, SwitchesChanged): return
            fancy_byte = event.fancy_byte
            bits = fancy_byte.to_binary_bits()
            for index, is_on in enumerate(bits):
                on_switch_change(index, is_on)
        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_switch_change)))

        # Text in effect
        def expect_text_in_change(state: Any, event: Any):
            if not isinstance(event, GoodChunkReceived): return
            if not isinstance(event.parsed_chunk, TextChunk): return
            self.input_text.label = f"Input: {event.parsed_chunk.text}"

        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_text_in_change)))


class MinOSApp(App):
    """TUI app for interacting with LEDs and buttons"""

    async def on_mount(self) -> None:
        """Mount the calculator widget."""
        await self.view.dock(ButtonLEDScreen())

    async def on_load(self):
        await self.bind("escape", "quit")

    def on_key(self, event):
        hacked_global_app_state_storage.message(ButtonPress(event.key))

    @staticmethod
    async def run_with_state(engine_state: EngineMonitorMinOSState):
        hacked_global_app_state_storage.update(engine_state)
        app = MinOSApp()

        LOGGER.info("Starting app")
        res = await engine_state.base.death.or_awaitable(app.process_messages())
        if isinstance(res, Err):
            await app.shutdown()
            LOGGER.info("Force stopping app")
        LOGGER.info("App finished")
        engine_state.base.death.grace()
