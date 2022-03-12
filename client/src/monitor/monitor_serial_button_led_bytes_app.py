"""Module for functionality related to serial socket monitor as button/led byte stream, specifically graphics/UI"""
import asyncio
import sys
from typing import Callable, Optional

from result import Err
from textual import events
from textual.app import App
from textual.views import GridView
from textual.widgets import Button
from src.domain.fancy_byte import FancyByte
from src.util import log
from src.domain.death import Death

LOGGER = log.timed_named_logger("monitor_button_led_bytes_app")


class AppState:
    death = Death()
    on_indexed_button_click = []
    on_indexed_led_change = []
    last_byte_in: FancyByte = FancyByte(0)
    last_byte_out: FancyByte = FancyByte(0)
    bytes_in = 0
    bytes_out = 0

    def stats(self):
        quit = "Quit with CTRL-C or Esc"
        i = str(int(self.bytes_in) - 1) if self.bytes_in > 0 else "?"
        o = str(int(self.bytes_out) - 1) if self.bytes_out > 0 else "?"
        lbi = f"last byte #{i} in: {self.last_byte_in.to_hex_str()}"
        lbo = f"last byte #{o} out: {self.last_byte_out.to_hex_str()}"
        return f"{quit}, {lbi}, {lbo}"

    def set_on_indexed_button_click(
            self,
            on_indexed_button_click: Callable[[int], None]
    ):
        self.on_indexed_button_click.append(on_indexed_button_click)

    def indexed_button_click(
            self,
            button_index: int
    ):
        if self.on_indexed_button_click is not None:
            for c in self.on_indexed_button_click:
                c(button_index)

    def set_on_indexed_led_change(
            self,
            on_indexed_led_change: Callable[[FancyByte, int, bool], None]
    ):
        self.on_indexed_led_change.append(on_indexed_led_change)

    def indexed_led_change(
            self,
            fancy_byte: FancyByte,
            led_index: int,
            led_on: bool
    ):
        if self.on_indexed_led_change is not None:
            for c in self.on_indexed_led_change:
                c(fancy_byte, led_index, led_on)


class AppStateStorage:
    state: Optional[AppState] = None

    def update(self, state: AppState):
        self.state = state


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

        self.stats = Button(hacked_global_app_state_storage.state.stats(), style=self.DARK, name=f"stats")

        def on_button_click(button_index: int):
            hacked_global_app_state_storage.state.last_byte_out = FancyByte.fromInt(button_index).value
            hacked_global_app_state_storage.state.bytes_out += 1
            self.stats.label = hacked_global_app_state_storage.state.stats()
        hacked_global_app_state_storage.state.set_on_indexed_button_click(on_button_click)

        def on_led_change(fancy_byte: FancyByte, led_index: int, led_on: bool):
            if 0 <= led_index < len(self.leds):
                self.leds[led_index].button_style = self.RED if led_on else self.DARK
                i = str(7 - led_index)
                s = "on" if led_on else "off"
                self.leds[led_index].label = f"LED{i} | {s}"
                hacked_global_app_state_storage.state.last_byte_in = fancy_byte
                hacked_global_app_state_storage.state.bytes_in += 1 / 8
                self.stats.label = hacked_global_app_state_storage.state.stats()

        hacked_global_app_state_storage.state.set_on_indexed_led_change(on_led_change)

        self.grid.place(stats=self.stats)


class ButtonLEDApp(App):
    """TUI app for interacting with LEDs and buttons"""

    async def on_mount(self) -> None:
        """Mount the calculator widget."""
        await self.view.dock(ButtonLEDScreen())

    async def on_load(self):
        await self.bind("escape", "quit")

    def on_key(self, event):
        if event.key in button_keys:
            button_index = button_keys.index(event.key)
            hacked_global_app_state_storage.state.indexed_button_click(button_index)

    @staticmethod
    async def run_with_state(app_state: AppState):
        hacked_global_app_state_storage.update(app_state)
        app = ButtonLEDApp()

        LOGGER.info("Starting app")
        res = await app_state.death.or_awaitable(app.process_messages())
        if isinstance(res, Err):
            await app.shutdown()
            LOGGER.info("Force stopping app")
        LOGGER.info("App finished")
        app_state.death.grace()


if __name__ == '__main__':
    app_state = AppState()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ButtonLEDApp.run_with_state(app_state))
    sys.exit(0)
