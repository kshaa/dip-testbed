"""A hint for pyinstaller to pack additional hidden imports/libraries"""
import monitor_serial_button_led_bytes_app

is_kivy_available = monitor_serial_button_led_bytes_app.is_kivy_available()

kivy_imports = [
    "kivy",
    "kivy.app.*",
    "kivy.uix.button.*",
    "kivy.uix.gridlayout.*",
    "kivy.uix.label.*",
    "kivy.core.window.*",
    "kivy.properties.*",
]

hiddenimports = kivy_imports if is_kivy_available else []
