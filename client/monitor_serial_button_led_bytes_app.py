"""Module for functionality related to serial socket monitoring as button/led byte stream, specifically graphics/UI"""

import asyncio
from typing import Callable, Optional
import log
from death import Death

LOGGER = log.timed_named_logger("monitor_button_led_bytes_app")


class AppState:
    death = Death()
    on_indexed_button_click = None
    on_indexed_led_change = None

    def set_on_indexed_button_click(
            self,
            on_indexed_button_click: Callable[[int], None]
    ):
        self.on_indexed_button_click = on_indexed_button_click

    def indexed_button_click(
            self,
            button_index: int
    ):
        if self.on_indexed_button_click is not None:
            self.on_indexed_button_click(button_index)

    def set_on_indexed_led_change(
            self,
            on_indexed_led_change: Callable[[int, bool], None]
    ):
        self.on_indexed_led_change = on_indexed_led_change

    def indexed_led_change(
            self,
            led_index: int,
            led_on: bool
    ):
        if self.on_indexed_led_change is not None:
            self.on_indexed_led_change(led_index, led_on)


class AppStateStorage:
    state: Optional[AppState] = None

    def update(self, state: AppState):
        self.state = state


hacked_global_app_state_storage = AppStateStorage()


def define_app():
    import kivy
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.core.window import Window
    from kivy.properties import NumericProperty

    kivy.require("2.0.0")

    class MyButton(Button):
        key_index = NumericProperty()

        def __init__(self, **kwargs):
            super(MyButton, self).__init__(**kwargs)

        def on_press(self):
            self.background_color = (1, 1, 1, 0.7)

        def on_release(self):
            hacked_global_app_state_storage.state.indexed_button_click(self.key_index)
            self.background_color = (1, 1, 1, 0.9)

    class ButtonLEDScreen(GridLayout):
        """Kivy screen for interacting with LEDs and buttons"""
        leds = [
            Button(
                background_down='',
                background_normal='',
                background_color=(1, 0, 0, 0.2),
                text=f'LED{i}',
                font_size=14,
                outline_color=(1, 1, 1, 1))
            for i in range(0, 8)
        ]
        button_keys = [
            "q", "w", "e", "r", "t", "y", "u", "i",
            "a", "s", "d", "f", "g", "h", "j", "k",
            "z", "x", "c", "v", "b", "n", "m", ",",
        ]
        buttons = [
            MyButton(
                background_down='',
                background_normal='',
                background_color=(1, 1, 1, 0.9),
                key_index=i,
                text=f'BTN{i} [{k}]',
                font_size=14,
                color=(0, 0, 0, 1))
            for (i, k) in enumerate(button_keys)
        ]

        def __init__(self, **kwargs):
            # Initialize Kivy GridLayout
            super(ButtonLEDScreen, self).__init__(**kwargs)

            # Set grid column count
            self.cols = 8

            # Add all LEDs
            for led in self.leds:
                self.add_widget(led)

            # Bind LED state handler
            def on_led_change(led_index: int, led_on: bool):
                led: Label = self.leds[led_index]
                LOGGER.debug(f"LED{led_index}: {led_on}")
                if led_on:
                    led.background_color = (1, 0, 0, 0.8)
                else:
                    led.background_color = (1, 0, 0, 0.2)

            hacked_global_app_state_storage.state.set_on_indexed_led_change(on_led_change)

            # Add all buttons
            for button in self.buttons:
                self.add_widget(button)

            # Bind keyboard button handler
            def on_key_up(_window, key, _scancode):
                self.on_key_action(True, key)
            Window.bind(on_key_up=on_key_up)

            def on_key_down(_window, key, _scancode, _codepoint, _modifier):
                self.on_key_action(False, key)
            Window.bind(on_key_down=on_key_down)

        def on_key_action(self, is_up: bool, key: int):
            def handle(button: Button):
                if is_up:
                    button.on_release()
                else:
                    button.on_press()

            try:
                key_index = self.button_keys.index(chr(key))
                handle(self.buttons[key_index])
            except ValueError as _e:
                pass


    class ButtonLEDApp(App):
        """GUI app for interacting with LEDs and buttons"""

        def build(self):
            return ButtonLEDScreen()

    def run_button_led_app(app_state: AppState):
        hacked_global_app_state_storage.update(app_state)
        app = ButtonLEDApp()

        async def app_lifecycle():
            LOGGER.info("Starting app")
            await app.async_run()
            LOGGER.info("Stopping app")
            app_state.death.grace()

        asyncio_loop = asyncio.get_event_loop()
        asyncio_loop.create_task(app_lifecycle())


    return (ButtonLEDApp, run_button_led_app)


async def waste_time_freely(app_state: AppState):
    """This method is also run by the asyncio loop and periodically prints something."""
    try:
        toggle = True
        while True:
            toggle = not toggle
            app_state.indexed_led_change(0, toggle)
            await asyncio.sleep(2)
    except asyncio.CancelledError as e:
        print('Wasting time was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done wasting time')

if __name__ == '__main__':
    app_state = AppState()
    hacked_global_app_state_storage.update(app_state)
    (ButtonLEDApp, _run_button_led_app) = define_app()
    app = ButtonLEDApp()
    asyncio_loop = asyncio.get_event_loop()
    asyncio_loop.run_until_complete(asyncio.gather(
        waste_time_freely(hacked_global_app_state_storage.state),
        app.async_run()
    ))
