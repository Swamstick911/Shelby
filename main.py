import machine
import time
import gc
import sys
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
        time.sleep(2)
except Exception as e:
    print(f"WiFi error: {e}")
    wifi_connected = False

# 5. Core Screens (Always loaded)
from src.clock   import ClockScreen
from src.menu    import MenuScreen
from src.weather import WeatherManager 

print("Shelby OS started.")
wdt = WDT(timeout=8000)

clock = ClockScreen(display)
menu_scr = MenuScreen(display, FONT)
weather_mgr = WeatherManager(secrets)

if wifi_connected:
    weather_mgr.update()
    clock.weather = weather_mgr.condition

clock.show_menu_hint(0)
clock.update()

# 6. Navigation state
current_view  = "Clock"
active_app    = None    # <-- Holds the dynamically loaded app
last_gh_fetch = time.ticks_ms() - 300000
last_we_fetch = time.ticks_ms()
gh_count      = 0


# --- HELPER: LAZY LOAD AN APP ---
def load_app(module_name, class_name, *args):
    """Dynamically imports an app module, instantiates it, and returns the object."""
    gc.collect()
    print(f"Loading {module_name}...")
    mod = __import__(f"src.{module_name}", None, None, [class_name])
    app_class = getattr(mod, class_name)
    app = app_class(*args)
    app.show()
    return app

# --- HELPER: UNLOAD AN APP ---
def unload_app():
    """Destroys the current app and forcefully removes it from RAM."""
    global active_app
    active_app = None
    
    # Identify modules that aren't core and delete them from sys.modules
    core_modules = ["sys", "gc", "machine", "time", "urequests", "st7735", 
                    "src.font", "src.clock", "src.menu", "src.weather", "src.wifi_manager", "secrets"]
    
    for mod_name in list(sys.modules.keys()):
        if mod_name not in core_modules and not mod_name.startswith("src.utils") and not mod_name.startswith("src.icons"):
            del sys.modules[mod_name]
            
    gc.collect()  # Nuke the dead app from RAM immediately!


# 7. Main loop
while True:
    wdt.feed()  # Pet the watchdog
    
    for b in btns.values():
        b.update()

    if current_view == "Clock":
        clock.update()

    # Background GitHub fetch
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_gh_fetch) > 300000:
        gc.collect()
        try:
            headers = {"Authorization": f"Bearer {secrets.get('github_token', '')}", "User-Agent": "Sprig-Shelby"}
            r = urequests.get("https://api.github.com/notifications?per_page=5", headers=headers, stream=True, timeout=5)
            if r.status_code == 200:
                gh_count = 0
                while True:
                    wdt.feed()
                    chunk = r.raw.read(128)
                    if not chunk: break
                    gh_count += chunk.decode("utf-8", "ignore").count('"id":')
            try: r.raw.close()
            except: pass
            r.close()
        except: pass
        gc.collect()
        last_gh_fetch = time.ticks_ms()
        if current_view == "Clock":
            clock.show_menu_hint(0, gh_count, 0)

    # Background Weather fetch
    if wifi_connected and time.ticks_diff(time.ticks_ms(), last_we_fetch) > 60000:
        gc.collect()
        if weather_mgr.update():
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
        elif current_view not in ["Clock", "Menu"]:
            pass # Active app handles J itself

    # --- PER-SCREEN INPUT ---
    if current_view == "Clock":
        if btns["L"].pressed():
            current_view = "Menu"
            menu_scr.show()
        
    elif current_view == "Menu":
        result = menu_scr.handle_input(btns)
        
        if result == "github" and wifi_connected:
            current_view = "GitHub"
            active_app = load_app("github", "GithubScreen", display, FONT, secrets)
            
        elif result == "system":
            current_view = "System"
            active_app = load_app("system", "SystemScreen", display, FONT)
            
        elif result == "tasks":
            current_view = "Tasks"
            active_app = load_app("tasks", "TaskScreen", display, FONT)
            
        elif result == "settings":
            current_view = "Settings"
            active_app = load_app("settings", "SettingsScreen", display, FONT, secrets, wifi_mgr)
            
        elif result == "hackatime":
            current_view = "Hackatime"
            active_app = load_app("hackatime", "HackatimeScreen", display, FONT, secrets, wdt)
            
        elif result == "music":
            current_view = "Music"
            # We must load settings first temporarily if music depends on it, or update music.py
            # For now, if Music requires st_scr, we create a dummy one or adapt it.
            active_app = load_app("music", "MusicScreen", display, FONT, None)

    # --- ACTIVE APP INPUT HANDLING ---
    elif active_app is not None:
        result = active_app.handle_input(btns)
        
        if result == "menu":
            # If we were in settings, apply the 24h change before closing
            if current_view == "Settings" and hasattr(active_app, "use_24h"):
                clock.use_24h = active_app.use_24h
                clock.needs_full_redraw = True
                clock.last_sec = -1
                
            unload_app() # FREE ALL THE RAM
            current_view = "Menu"
            menu_scr.show()

    time.sleep_ms(20)