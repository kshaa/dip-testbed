"""Module for functionality related to serial socket monitor as button/led byte stream, specifically graphics/UI"""
import asyncio
import sys
from functools import partial
from typing import Callable, Optional, Any

from result import Err
from textual import events
from textual.app import App
from textual.views import GridView
from textual.widgets import Button
from src.domain.fancy_byte import FancyByte
from src.domain.minos_chunks import LEDChunk
from src.domain.minos_monitor_event import GoodChunkReceived
from src.domain.monitor_message import IndexButtonClick, AddTUISideEffect
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.util import log
from src.domain.death import Death

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
button_keys = [
    "q", "w", "e", "r", "t", "y", "u", "i",
    "a", "s", "d", "f", "g", "h", "j", "k",
    "z", "x", "c", "v", "b", "n", "m", ",",
]


class ButtonLEDScreen(GridView):
    """Screen for interacting with LEDs and buttons"""

    # Colors
    DARK = "white on rgb(51,51,51)"
    LIGHT = "black on rgb(165,165,165)"
    RED = "white on rgb(215,0,0)"

    def on_mount(self, event: events.Mount) -> None:
        """Event when widget is first mounted (added to a parent view)."""
        # Make all the LEDs
        self.leds = [
            Button(f"LED{7 - i} | off", style=self.DARK, name=f"LED{7 - i}")
            for i in range(0, 8)
        ]

        # Make all the buttons
        self.buttons = [
            Button(f"BTN{i} | {k}", style=self.LIGHT, name=f"BTN{i} | {k}")
            for (i, k) in enumerate(button_keys)
        ]

        # Set basic grid settings
        self.grid.set_gap(2, 1)
        self.grid.set_gutter(1)
        self.grid.set_align("center", "center")

        # Create rows / columns / areas
        self.grid.add_column("col", max_size=30, repeat=8)
        self.grid.add_row("buttons", max_size=15, repeat=4)
        self.grid.add_row("statsrow", max_size=30, repeat=1)
        self.grid.add_areas(
            stats="col1-start|col8-end,statsrow",
        )

        # Place out widgets in to the layout
        for led in self.leds:
            self.grid.place(led)

        for button in self.buttons:
            self.grid.place(button)

        self.stats = Button("", style=self.DARK, name=f"stats")

        def on_led_change(fancy_byte: FancyByte, led_index: int, led_on: bool):
            if 0 <= led_index < len(self.leds):
                self.leds[led_index].button_style = self.RED if led_on else self.DARK
                i = str(7 - led_index)
                s = "on" if led_on else "off"
                self.leds[led_index].label = f"LED{i} | {s}"
                # hacked_global_app_state_storage.state.last_byte_in = fancy_byte
                # hacked_global_app_state_storage.state.bytes_in += 1 / 8
                # self.stats.label = hacked_global_app_state_storage.state.stats()

        def expect_button_click(event: Any):
            # print(event)
            if not isinstance(event, GoodChunkReceived): return
            if not isinstance(event.parsed_chunk, LEDChunk): return
            fancy_byte = event.parsed_chunk.fancy_byte
            bits = fancy_byte.to_binary_bits()
            for index, is_on in enumerate(bits):
                on_led_change(fancy_byte, index, is_on)

        hacked_global_app_state_storage.message(AddTUISideEffect(partial(expect_button_click)))

        self.grid.place(stats=self.stats)


class MinOSApp(App):
    """TUI app for interacting with LEDs and buttons"""

    async def on_mount(self) -> None:
        """Mount the calculator widget."""
        await self.view.dock(ButtonLEDScreen())

    async def on_load(self):
        await self.bind("escape", "quit")

    def on_key(self, event):
        if event.key in button_keys:
            button_index = button_keys.index(event.key)
            hacked_global_app_state_storage.message(IndexButtonClick(button_index))

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
