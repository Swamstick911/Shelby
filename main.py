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

# 5. Core Screens
from src.clock   import ClockScreen
from src.menu    import MenuScreen

print("Shelby OS started.")

wdt = None

clock = ClockScreen(display)
menu_scr = MenuScreen(display, FONT)

clock.show_menu_hint(0)
clock.update()

# 6. Navigation state
current_view  = "Clock"
active_app    = None    
last_gh_fetch = time.ticks_ms() - 300000
gh_count      = 0

#HELPER: LAZY LOAD AN APP
def load_app(module_name, class_name, *args):
    gc.collect()
    print(f"Loading {module_name}...")
    try:
        mod = __import__(f"src.{module_name}", None, None, [class_name])
        app_class = getattr(mod, class_name)
        app = app_class(*args)
        app.show()
        return app
    except Exception as e:
        print(f"Failed to load {module_name}: {e}")
        return None

def unload_app():
    global active_app
    active_app = None
    
    core_modules = ["sys", "gc", "machine", "time", "urequests", "st7735", 
                    "src.font", "src.clock", "src.menu", "src.wifi_manager", "secrets"]
    
    for mod_name in list(sys.modules.keys()):
        if mod_name not in core_modules and not mod_name.startswith("src.utils") and not mod_name.startswith("src.icons"):
            del sys.modules[mod_name]
            
    gc.collect() 

# 7. Main loop
while True:
    if wdt:
        wdt.feed() 
    
    for b in btns.values():
        b.update()

    if current_view == "Clock":
        clock.update()

    # J button - Global back to menu
    if btns["J"].pressed():
        if current_view == "Menu":
            current_view = "Clock"
            clock.last_sec = -1
            clock.needs_full_redraw = True
            clock.show_menu_hint(0, gh_count, 0)
            clock.update()
        elif current_view not in ["Clock", "Menu"]:
            pass 

    #Per screen handling
    if current_view == "Clock":
        if btns["L"].pressed():
            current_view = "Menu"
            menu_scr.show()
        
    elif current_view == "Menu":
        result = menu_scr.handle_input(btns)
        
        if result == "github" and wifi_connected:
            current_view = "GitHub"
            active_app = load_app("github", "GithubScreen", display, FONT, secrets, wdt)
            
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
            active_app = load_app("music", "MusicScreen", display, FONT, None)
            
        if result and current_view not in ["Clock", "Menu"] and active_app is None:
            current_view = "Menu"
            menu_scr.show()

    #app input handling
    elif active_app is not None:
        result = active_app.handle_input(btns)
        
        if result == "menu":
            if current_view == "Settings" and hasattr(active_app, "use_24h"):
                clock.use_24h = active_app.use_24h
                clock.needs_full_redraw = True
                clock.last_sec = -1
                
            unload_app() 
            current_view = "Menu"
            menu_scr.show()

    time.sleep_ms(20)