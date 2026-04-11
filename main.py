import machine
import time
import gc
import urequests
from machine import Pin, SPI, WDT
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
from src.games    import GamesScreen
from src.tasks    import TaskScreen
from src.settings import SettingsScreen
from src.hackatime import HackatimeScreen
from src.music import MusicScreen
from src.weather import WeatherManager 

clock = ClockScreen(display)
menu_scr = MenuScreen(display, FONT)
gh_scr = GithubScreen(display, FONT, secrets)
games_scr = GamesScreen(display, FONT)
tk_scr = TaskScreen(display, FONT)
st_scr = SettingsScreen(display, FONT, secrets, wifi_mgr)
ht_scr = HackatimeScreen(display, FONT, secrets)
mu_scr = MusicScreen(display, FONT, st_scr)
weather_mgr = WeatherManager(secrets)

if wifi_connected:
    weather_mgr.update()
    clock.weather = weather_mgr.condition

clock.show_menu_hint(0)
clock.update()


# 6. Navigation state
current_view  = "Clock"
last_gh_fetch = time.ticks_ms() - 300000
last_we_fetch = time.ticks_ms()
gh_count      = 0

print("Shelby OS started.")

# Hardware Watchdog - Will reboot the Pico if the loop hangs for 8 seconds
wdt = WDT(timeout=8000)

# 7. Main loop
while True:
    wdt.feed()  # Pet the watchdog
    
    for b in btns.values():
        b.update()

    if current_view == "Clock":
        clock.update()

    # Background GitHub fetch every 5 min
        # Background GitHub fetch every 5 min
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_gh_fetch) > 300000:
        gc.collect()
        try:
            headers = {
                "Authorization": f"Bearer {secrets.get('github_token', '')}",
                "User-Agent": "Sprig-Shelby"
            }
            # Add timeout to prevent socket hangs
            r = urequests.get(
                "https://api.github.com/notifications?per_page=5",
                headers=headers,
                stream=True,
                timeout=5
            )
            
            if r.status_code == 200:
                gh_count = 0
                while True:
                    wdt.feed() # Keep watchdog happy during slow downloads
                    chunk = r.raw.read(128) # Dropped from 256 to 128 bytes to save even more RAM
                    if not chunk:
                        break
                    gh_count += chunk.decode("utf-8", "ignore").count('"id":')
                    del chunk
            
            # The critical memory fix: explicitly close the raw socket AND the response
            try:
                r.raw.close()
            except:
                pass
            r.close()
            del r
            
        except Exception as e:
            print(f"Badge fetch error: {e}")
            
        gc.collect()
        last_gh_fetch = time.ticks_ms()
        if current_view == "Clock":
            clock.show_menu_hint(0, gh_count, 0)

    # Background Weather fetch every 60 seconds (Manager enforces 15m API limit internally)
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_we_fetch) > 60000:
        gc.collect()
        changed = weather_mgr.update()
        if changed:
            clock.weather = weather_mgr.condition
            clock._particles = []          
            clock.needs_full_redraw = True
        
        gc.collect()
        last_we_fetch = time.ticks_ms()

    # J button - Global back to menu
    if btns["J"].pressed():
        if current_view == "Menu":
            current_view = "Clock"
            clock.last_sec = -1
            clock.needs_full_redraw = True
            clock.show_menu_hint(0, gh_count, 0)
            clock.update()
        elif current_view in ["Settings", "GitHub", "Games", "Tasks", "Hackatime", "Music"]:
            pass # Active screen handles J itself

    # Per-screen input
    if current_view == "Clock":
        if btns["L"].pressed():
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

        elif result == "games":
            if not wifi_connected:
                current_view = "Menu"
            else:
                current_view = "Games"
                games_scr.show()

        elif result == "tasks":
            current_view = "Tasks"
            tk_scr.show()

        elif result == "settings":
            current_view = "Settings"
            st_scr.show()
        
        elif result == "hackatime":
            current_view = "Hackatime"
            ht_scr.show()
        
        elif result == "music":
            current_view = "Music"
            mu_scr.show()

    # Active screen input handling
    elif current_view == "GitHub":
        result = gh_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Games":
        result = games_scr.handle_input(btns)
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

    elif current_view == "Hackatime":
        result = ht_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    elif current_view == "Music":
        result = mu_scr.handle_input(btns)
        if result == "menu":
            current_view = "Menu"
            menu_scr.show()

    time.sleep_ms(20)