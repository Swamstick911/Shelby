# code.py
import time
import board
import displayio
import keypad
import rtc

# Load secrets
try:
    from secrets import secrets
except ImportError:
    print("ERROR: secrets.py not found.")
    while True: time.sleep(1)

# Set time manually since WiFi isn't available on Sprig firmware
# Update these numbers to your current time before saving!
# Format: (year, month, day, hour, minute, second, weekday, yearday, isdst)
# Hour is 24hr format — 21 = 9 PM
r = rtc.RTC()
r.datetime = time.struct_time((2026, 3, 26, 21, 44, 0, 0, 0, -1))
print("Time set manually.")

display = board.DISPLAY

BUTTONS = (
    board.BUTTON_W, board.BUTTON_A, board.BUTTON_S, board.BUTTON_D,
    board.BUTTON_I, board.BUTTON_J, board.BUTTON_K, board.BUTTON_L
)
keys = keypad.Keys(BUTTONS, value_when_pressed=False, pull=True)

from src.clock import ClockScreen
clock_screen = ClockScreen(display.width, display.height)
display.root_group = clock_screen
clock_screen.update()

MENU_ITEMS = ["Clock", "GitHub", "Gmail", "Tasks"]
menu_index = 0
current_view = "Clock"

clock_screen.show_menu_hint(menu_index)
print("Shelby OS Started.")

while True:
    if current_view == "Clock":
        clock_screen.update()

    event = keys.events.get()
    if event and event.pressed:
        key_pin = BUTTONS[event.key_number]

        if key_pin == board.BUTTON_A:
            if current_view != "Clock":
                current_view = "Clock"
                menu_index = 0
                display.root_group = clock_screen
                clock_screen.show_menu_hint(menu_index)

        elif current_view == "Clock":
            if key_pin == board.BUTTON_W:
                menu_index = (menu_index - 1) % len(MENU_ITEMS)
                clock_screen.show_menu_hint(menu_index)

            elif key_pin == board.BUTTON_S:
                menu_index = (menu_index + 1) % len(MENU_ITEMS)
                clock_screen.show_menu_hint(menu_index)

            elif key_pin == board.BUTTON_D:
                selected = MENU_ITEMS[menu_index]
                print(f"Selected: {selected}")
                current_view = selected

    time.sleep(0.02)
