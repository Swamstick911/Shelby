import machine
import time
from machine import Pin, SPI
import st7735
from src.font import FONT

# Display init - constructor takes pin NUMBERS not Pin objects

spi = SPI(0,
    baudrate=8000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19),
    miso=Pin(16)
)

# TFT(spi, DC_pin_number, Reset_pin_number, CS_pin_number)
display = st7735.TFT(spi, 22, 26, 20)
display.initg()
display.rgb(False)   # BGR mode for Sprig panel
display.rotation(1) #fixing the landscape orientation
display.fill(st7735.TFT.BLACK)

# Buttons — exact pins from Sprig HAL source

BUTTON_W = Pin(5,  Pin.IN, Pin.PULL_UP)
BUTTON_A = Pin(6,  Pin.IN, Pin.PULL_UP)
BUTTON_S = Pin(7,  Pin.IN, Pin.PULL_UP)
BUTTON_D = Pin(8,  Pin.IN, Pin.PULL_UP)
BUTTON_I = Pin(12, Pin.IN, Pin.PULL_UP)
BUTTON_J = Pin(13, Pin.IN, Pin.PULL_UP)
BUTTON_K = Pin(14, Pin.IN, Pin.PULL_UP)
BUTTON_L = Pin(15, Pin.IN, Pin.PULL_UP)

# Simple debounce helper

class Button:
    def __init__(self, pin):
        self.pin = pin
        self._last = True
        self._pressed = False

    def update(self):
        val = self.pin.value()
        self._pressed = (self._last == True and val == False)
        self._last = val

    def pressed(self):
        return self._pressed

btns = {
    "W": Button(BUTTON_W),
    "A": Button(BUTTON_A),
    "S": Button(BUTTON_S),
    "D": Button(BUTTON_D),
    "I": Button(BUTTON_I),
    "J": Button(BUTTON_J),
    "K": Button(BUTTON_K),
    "L": Button(BUTTON_L),
}

# Load secrets

try:
    from secrets import secrets
except ImportError:
    display.fill(st7735.TFT.BLACK)
    display.text((10, 50), "secrets.py", st7735.TFT.WHITE, FONT, 1)
    display.text((10, 62), "not found!", st7735.TFT.WHITE, FONT, 1)
    while True:
        time.sleep(1)

# WiFi + time sync

wifi_connected = False

try:
    from src.wifi_manager import WifiManager
    wifi_mgr = WifiManager(secrets)
    display.fill(st7735.TFT.BLACK)
    display.text((10, 50), "Connecting to", st7735.TFT.WHITE, FONT, 1)
    display.text((10, 62), "WiFi...", st7735.TFT.WHITE, FONT, 1)
    wifi_connected = wifi_mgr.connect()
    if wifi_connected:
        display.fill(st7735.TFT.BLACK)
        display.text((5, 57), "Syncing time...", st7735.TFT.WHITE, FONT, 1)
        wifi_mgr.sync_time()
    else:
        display.fill(st7735.TFT.BLACK)
        display.text((10, 50), "WiFi failed.", st7735.TFT.RED, FONT, 1)
        display.text((10, 62), "Offline mode.", st7735.TFT.RED, FONT, 1)
        time.sleep(2)
except Exception as e:
    print(f"WiFi error: {e}")
    wifi_connected = False

# Clock screen

from src.clock import ClockScreen
clock = ClockScreen(display)
clock.update()

# Navigation state

MENU_ITEMS   = ["Clock", "GitHub", "Gmail", "Tasks"]
menu_index   = 0
current_view = "Clock"

clock.show_menu_hint(menu_index)
print("Shelby OS started.")

last_api_fetch = time.ticks_ms()
gh_count   = 0
mail_count = 0

# Main loop

while True:
    for b in btns.values():
        b.update()

    if current_view == "Clock":
        clock.update()

    # Refresh API badge counts every 5 minutes
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_api_fetch) > 300000:
        try:
            import urequests
            import gc
            gc.collect()
            headers = {
                "Authorization": f"Bearer {secrets.get('github_token', '')}",
                "User-Agent": "Sprig-Shelby"
            }
            r = urequests.get("https://api.github.com/notifications", headers=headers)
            if r.status_code == 200:
                gh_count = len(r.json())
            r.close()
            gc.collect()
        except Exception as e:
            print(f"API refresh failed: {e}")
        last_api_fetch = time.ticks_ms()
        if current_view == "Clock":
            clock.show_menu_hint(menu_index, gh_count, mail_count)

    # Button handling

    if btns["A"].pressed():
        if current_view != "Clock":
            current_view = "Clock"
            menu_index = 0
            display.fill(st7735.TFT.BLACK)
            clock._last_hour = -1
            clock.update()
            clock.show_menu_hint(menu_index, gh_count, mail_count)

    elif current_view == "Clock":
        if btns["W"].pressed():
            menu_index = (menu_index - 1) % len(MENU_ITEMS)
            clock.show_menu_hint(menu_index, gh_count, mail_count)

        elif btns["S"].pressed():
            menu_index = (menu_index + 1) % len(MENU_ITEMS)
            clock.show_menu_hint(menu_index, gh_count, mail_count)

        elif btns["D"].pressed():
            selected = MENU_ITEMS[menu_index]

            if selected == "Clock":
                pass

            elif selected == "GitHub":
                if not wifi_connected:
                    clock.status_text = "No WiFi!"
                    clock.show_menu_hint(menu_index)
                else:
                    current_view = "GitHub"
                    display.fill(st7735.TFT.BLACK)
                    display.text((55, 5),  "GitHub",     st7735.TFT.WHITE, FONT, 1)
                    display.text((35, 60), "Loading...", st7735.TFT.GREEN, FONT, 1)

            elif selected == "Gmail":
                if not wifi_connected:
                    clock.status_text = "No WiFi!"
                    clock.show_menu_hint(menu_index)
                else:
                    current_view = "Gmail"
                    display.fill(st7735.TFT.BLACK)
                    display.text((58, 5),  "Gmail",      st7735.TFT.WHITE, FONT, 1)
                    display.text((35, 60), "Loading...", st7735.TFT.GREEN, FONT, 1)

            elif selected == "Tasks":
                current_view = "Tasks"
                display.fill(st7735.TFT.BLACK)
                display.text((58, 5),  "Tasks",        st7735.TFT.WHITE, FONT, 1)
                display.text((25, 60), "Coming soon!", st7735.TFT.GREEN, FONT, 1)

    time.sleep_ms(20)