import machine
import time
from machine import Pin, SPI
import st7735
from src.font import FONT


# 1. Display init FIRST
spi = SPI(0, baudrate=8000000, polarity=0, phase=0,
    sck=Pin(18), mosi=Pin(19), miso=Pin(16))
display = st7735.TFT(spi, 22, 26, 20)
display.initg()
display.rgb(False)
display.rotation(1)
display.fill(st7735.TFT.BLACK)


# 2. Buttons
BUTTON_W = Pin(5,  Pin.IN, Pin.PULL_UP)
BUTTON_A = Pin(6,  Pin.IN, Pin.PULL_UP)
BUTTON_S = Pin(7,  Pin.IN, Pin.PULL_UP)
BUTTON_D = Pin(8,  Pin.IN, Pin.PULL_UP)
BUTTON_I = Pin(12, Pin.IN, Pin.PULL_UP)
BUTTON_J = Pin(13, Pin.IN, Pin.PULL_UP)
BUTTON_K = Pin(14, Pin.IN, Pin.PULL_UP)
BUTTON_L = Pin(15, Pin.IN, Pin.PULL_UP)


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
    "W": Button(BUTTON_W), "A": Button(BUTTON_A),
    "S": Button(BUTTON_S), "D": Button(BUTTON_D),
    "I": Button(BUTTON_I), "J": Button(BUTTON_J),
    "K": Button(BUTTON_K), "L": Button(BUTTON_L),
}


# 3. Secrets
try:
    from secrets import secrets
except ImportError:
    display.fill(st7735.TFT.BLACK)
    display.text((10, 50), "secrets.py", st7735.TFT.WHITE, FONT, 1)
    display.text((10, 62), "not found!", st7735.TFT.WHITE, FONT, 1)
    while True: time.sleep(1)


# 4. WiFi + NTP
wifi_connected = False
wifi_mgr       = None
try:
    from src.wifi_manager import WifiManager
    wifi_mgr = WifiManager(secrets)
    display.fill(st7735.TFT.BLACK)
    display.text((10, 50), "Connecting to", st7735.TFT.WHITE, FONT, 1)
    display.text((10, 62), "WiFi...",       st7735.TFT.WHITE, FONT, 1)
    wifi_connected = wifi_mgr.connect()
    if wifi_connected:
        display.fill(st7735.TFT.BLACK)
        display.text((5, 57), "Syncing time...", st7735.TFT.WHITE, FONT, 1)
        wifi_mgr.sync_time()
    else:
        display.fill(st7735.TFT.BLACK)
        display.text((10, 50), "WiFi failed.",  st7735.TFT.RED, FONT, 1)
        display.text((10, 62), "Offline mode.", st7735.TFT.RED, FONT, 1)
        time.sleep(2)
except Exception as e:
    print(f"WiFi error: {e}")
    wifi_connected = False


# 5. All screens
from src.clock    import ClockScreen
from src.menu     import MenuScreen
from src.github   import GithubScreen
from src.gmail    import GmailScreen
from src.tasks    import TaskScreen
from src.settings import SettingsScreen

clock    = ClockScreen(display)
menu_scr = MenuScreen(display, FONT)
gh_scr   = GithubScreen(display, FONT, secrets)
gm_scr   = GmailScreen(display, FONT, secrets)
tk_scr   = TaskScreen(display, FONT)
st_scr   = SettingsScreen(display, FONT, secrets, wifi_mgr)

clock.show_menu_hint(0)
clock.update()


# 6. Navigation state
current_view   = "Clock"
last_api_fetch = time.ticks_ms()
gh_count       = 0
mail_count     = 0

print("Shelby OS started.")


# 7. Main loop
while True:
    for b in btns.values():
        b.update()

    if current_view == "Clock":
        clock.update()

    # Background GitHub fetch every 5 min
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_api_fetch) > 300000:
        try:
            import urequests, gc
            gc.collect()
            headers = {
                "Authorization": f"Bearer {secrets.get('github_token', '')}",
                "User-Agent": "Sprig-Shelby"
            }
            r = urequests.get(
                "https://api.github.com/notifications?per_page=5",
                headers=headers
            )
            if r.status_code == 200:
                gh_count = len(r.json())
            r.close()
            gc.collect()
        except Exception as e:
            print(f"API refresh failed: {e}")
        last_api_fetch = time.ticks_ms()
        if current_view == "Clock":
            clock.show_menu_hint(0, gh_count, mail_count)

    # ── A button: layered back navigation ────────────────────────
    if btns["A"].pressed():
        if current_view == "Clock":
            pass
        elif current_view == "Menu":
            current_view = "Clock"
            clock.last_sec = -1
            clock.needs_full_redraw = True
            clock.show_menu_hint(0, gh_count, mail_count)
            clock.update()
        else:
            current_view = "Menu"
            menu_scr.show()

    #Per-screen input
    elif current_view == "Clock":
        if btns["D"].pressed():
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Menu":
        result = menu_scr.handle_input(btns)
        if result == "github":
            if not wifi_connected:
                current_view = "Menu"
            else:
                current_view = "GitHub"
                gh_scr.show()

        elif result == "gmail":
            if not wifi_connected:
                current_view = "Menu"
            else:
                current_view = "Gmail"
                gm_scr.show()

        elif result == "tasks":
            current_view = "Tasks"
            tk_scr.show()

        elif result == "settings":
            current_view = "Settings"
            st_scr.show()

    #Active screen input handling
    elif current_view == "GitHub":
        result = gh_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Gmail":
        result = gm_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Tasks":
        result = tk_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Settings":
        result = st_scr.handle_input(btns)
        if result == "menu":
            clock.use_24h = st_scr.use_24h
            clock.needs_full_redraw = True
            clock.last_sec = -1
            current_view = "Menu"
            menu_scr.show()

    time.sleep_ms(20)