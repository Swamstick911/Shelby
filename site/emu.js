/* ============================================================
   Shelby — real firmware emulator
   Runs the actual MicroPython firmware (main loop + src/*.py +
   st7735 driver semantics) on MicroPython compiled to WebAssembly.
   Hardware is faked by small shim modules + a JS bridge:
     - st7735  -> draws to a 160x128 canvas
     - machine -> Pin reads page buttons; SPI/WDT/RTC/ADC/I2S stubbed
     - network/socket -> report "connected"; NTP is stubbed
     - urequests -> returns sample GitHub / Hackatime payloads
   The firmware's blocking `while True` loop is exposed as step()
   and driven from JS so the tab never freezes.
   ============================================================ */

const MP_URL = "https://cdn.jsdelivr.net/npm/@micropython/micropython-webassembly-pyscript@1.24.0/micropython.mjs";

// real firmware files to mount (fetched from /firmware/)
const FW_FILES = [
  "src/__init__.py", "src/font.py", "src/songs.py", "src/utils.py", "src/icons.py",
  "src/clock.py", "src/menu.py", "src/github.py", "src/hackatime.py",
  "src/system.py", "src/tasks.py", "src/settings.py", "src/music.py",
  "src/wifi_manager.py", "tasks.json",
];

/* ---------------- shim module sources (emulator, not firmware) ---------------- */

const SHIM_ST7735 = `
import hwbridge
def TFTColor(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)
class TFT:
    BLACK = 0
    RED = TFTColor(0xFF,0,0); MAROON = TFTColor(0x80,0,0)
    GREEN = TFTColor(0,0xFF,0); FOREST = TFTColor(0,0x80,0x80)
    BLUE = TFTColor(0,0,0xFF); NAVY = TFTColor(0,0,0x80)
    CYAN = TFTColor(0,0xFF,0xFF); YELLOW = TFTColor(0xFF,0xFF,0)
    PURPLE = TFTColor(0xFF,0,0xFF); WHITE = TFTColor(0xFF,0xFF,0xFF)
    GRAY = TFTColor(0x80,0x80,0x80)
    @staticmethod
    def color(r, g, b):
        return TFTColor(r, g, b)
    def __init__(self, spi=None, dc=0, reset=0, cs=0):
        self._size = (160, 128)
    def size(self): return self._size
    def initr(self): pass
    def initb(self): pass
    def initb2(self): pass
    def initg(self): pass
    def on(self, t=True): pass
    def invertcolor(self, b): pass
    def rgb(self, t=True): hwbridge.set_rgb(1 if t else 0)
    def rotation(self, r):
        if r & 1: self._size = (160, 128)
    def pixel(self, pos, color):
        x, y = pos
        if 0 <= x < self._size[0] and 0 <= y < self._size[1]:
            hwbridge.px(int(x), int(y), int(color))
    def fillrect(self, pos, size, color):
        x = _clamp(int(pos[0]), 0, self._size[0]); y = _clamp(int(pos[1]), 0, self._size[1])
        w = int(size[0]); h = int(size[1])
        if w < 0: x += w; w = -w
        if h < 0: y += h; h = -h
        if x + w > self._size[0]: w = self._size[0] - x
        if y + h > self._size[1]: h = self._size[1] - y
        if w > 0 and h > 0: hwbridge.fillrect(x, y, w, h, int(color))
    def fill(self, color=0):
        hwbridge.fillrect(0, 0, self._size[0], self._size[1], int(color))
    def hline(self, pos, length, color):
        if length < 0: self.fillrect((pos[0]+length, pos[1]), (-length, 1), color)
        else: self.fillrect(pos, (length, 1), color)
    def vline(self, pos, length, color):
        if length < 0: self.fillrect((pos[0], pos[1]+length), (1, -length), color)
        else: self.fillrect(pos, (1, length), color)
    def rect(self, pos, size, color):
        self.hline(pos, size[0], color)
        self.hline((pos[0], pos[1]+size[1]-1), size[0], color)
        self.vline(pos, size[1], color)
        self.vline((pos[0]+size[0]-1, pos[1]), size[1], color)
    def line(self, start, end, color):
        x0, y0 = int(start[0]), int(start[1]); x1, y1 = int(end[0]), int(end[1])
        if x0 == x1: self.vline((x0, min(y0,y1)), abs(y1-y0)+1, color); return
        if y0 == y1: self.hline((min(x0,x1), y0), abs(x1-x0)+1, color); return
        dx = abs(x1-x0); dy = abs(y1-y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.pixel((x0, y0), color)
            if x0 == x1 and y0 == y1: break
            e2 = 2*err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy
    def image(self, x0, y0, x1, y1, data): pass
    def char(self, pos, ch, color, font, sizes):
        if font is None: return
        if isinstance(sizes, (int, float)): sx = int(sizes); sy = int(sizes)
        else: sx, sy = int(sizes[0]), int(sizes[1])
        if sx < 1: sx = 1
        if sy < 1: sy = 1
        start = font["Start"]; end = font["End"]
        ci = ord(ch)
        if not (start <= ci <= end): return
        fw = font["Width"]; fh = font["Height"]
        ci = (ci - start) * fw
        data = font["Data"][ci:ci+fw]
        x0 = int(pos[0]); y0 = int(pos[1])
        for q in range(fw):
            c = data[q]
            for r in range(fh):
                if c & 1:
                    if sx == 1 and sy == 1: self.pixel((x0 + q, y0 + r), color)
                    else: self.fillrect((x0 + q*sx, y0 + r*sy), (sx, sy), color)
                c >>= 1
    def text(self, pos, string, color, font, size=1, nowrap=False):
        if font is None: return
        if isinstance(size, (int, float)): sx = int(size)
        else: sx = int(size[0])
        if sx < 1: sx = 1
        width = sx * font["Width"] + 1
        px = int(pos[0]); py = int(pos[1])
        for ch in string:
            self.char((px, py), ch, color, font, size)
            px += width
            if px + width > self._size[0]:
                if nowrap: break
                py += font["Height"] * (size if isinstance(size,int) else size[1]) + 1
                px = int(pos[0])
    def circle(self, pos, radius, color):
        import math
        xend = int(0.7071 * radius) + 1; rsq = radius*radius
        for x in range(xend):
            y = int(math.sqrt(rsq - x*x))
            for a,b in ((x,y),(x,-y),(-x,y),(-x,-y),(y,x),(y,-x),(-y,x),(-y,-x)):
                self.pixel((pos[0]+a, pos[1]+b), color)
    def fillcircle(self, pos, radius, color):
        import math
        rsq = radius*radius
        for x in range(-radius, radius+1):
            y = int(math.sqrt(max(0, rsq - x*x)))
            self.vline((pos[0]+x, pos[1]-y), 2*y+1, color)
`;

const SHIM_MACHINE = `
import hwbridge
class Pin:
    IN = 0; OUT = 1; PULL_UP = 2; PULL_DOWN = 3
    def __init__(self, id, mode=-1, pull=-1, *a, **k):
        self.id = id
    def value(self, v=None):
        if v is None: return hwbridge.pin_get(self.id)
        return None
    def __call__(self, v=None): return self.value(v)
    def on(self): pass
    def off(self): pass
class SPI:
    def __init__(self, *a, **k): pass
    def init(self, *a, **k): pass
    def write(self, buf): pass
    def read(self, n, *a): return b"\\x00" * n
class WDT:
    def __init__(self, *a, **k): pass
    def feed(self): pass
class RTC:
    def __init__(self, *a, **k): pass
    def datetime(self, dt=None): return None
class ADC:
    def __init__(self, ch, *a, **k): self.ch = ch
    def read_u16(self): return hwbridge.adc_read(self.ch)
class I2S:
    TX = 1; RX = 2; MONO = 0; STEREO = 1
    def __init__(self, *a, **k): pass
    def write(self, buf):
        try: return len(buf)
        except: return 0
    def deinit(self): pass
class Timer:
    def __init__(self, *a, **k): pass
    def init(self, *a, **k): pass
    def deinit(self): pass
def freq(f=None):
    if f is None: return hwbridge.get_freq()
    hwbridge.set_freq(f); return None
def unique_id(): return b"\\xde\\xad\\xbe\\xef\\x12\\x34"
def reset(): pass
def soft_reset(): pass
`;

const SHIM_NETWORK = `
STA_IF = 0; AP_IF = 1
class WLAN:
    def __init__(self, mode=0): self._on = False
    def active(self, v=None):
        if v is not None: self._on = bool(v)
        return self._on
    def isconnected(self): return True
    def connect(self, ssid=None, pw=None): return True
    def disconnect(self): pass
    def ifconfig(self, *a): return ("192.168.1.42", "255.255.255.0", "192.168.1.1", "1.1.1.1")
    def status(self, what=None):
        if what == "rssi": return -58
        return 3
    def config(self, *a, **k): return None
`;

const SHIM_SOCKET = `
AF_INET = 2; SOCK_STREAM = 1; SOCK_DGRAM = 2
def getaddrinfo(host, port, *a):
    raise OSError("emulator: no raw sockets")
class socket:
    def __init__(self, *a, **k): pass
    def settimeout(self, t): pass
    def connect(self, addr): raise OSError("emulator")
    def sendto(self, data, addr): raise OSError("emulator")
    def recv(self, n): raise OSError("emulator")
    def send(self, data): raise OSError("emulator")
    def close(self): pass
`;

const SHIM_UREQUESTS = `
import hwbridge
class _Raw:
    def __init__(self, data):
        self._d = data; self._p = 0
    def read(self, n=128):
        c = self._d[self._p:self._p+n]; self._p += n
        return c
    def close(self): pass
class Response:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self._b = body if isinstance(body, bytes) else body.encode()
        self.raw = _Raw(self._b)
        self.headers = headers or {}
        self.encoding = "utf-8"
    @property
    def text(self): return self._b.decode()
    @property
    def content(self): return self._b
    def json(self):
        import json; return json.loads(self._b.decode())
    def close(self): pass
def _go(url, method):
    body = hwbridge.http_sample(str(url), method)
    return Response(200, body if body else "{}")
def get(url, **k): return _go(url, "GET")
def post(url, **k): return _go(url, "POST")
def head(url, **k): return _go(url, "HEAD")
def request(method, url, **k): return _go(url, method)
`;

const SHIM_MICROPYTHON = `
def native(f): return f
def viper(f): return f
def const(x): return x
def mem_info(*a, **k): pass
def qstr_info(*a, **k): pass
def alloc_emergency_exception_buf(n): pass
def schedule(fn, arg): fn(arg)
def kbd_intr(n): pass
`;

const SHIM_UJSON = `from json import load, dump, loads, dumps`;

const SHIM_UBINASCII = `
_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
def b2a_base64(data):
    out = bytearray()
    n = len(data); i = 0
    while i < n:
        b0 = data[i]; b1 = data[i+1] if i+1 < n else 0; b2 = data[i+2] if i+2 < n else 0
        out.append(ord(_B64[b0 >> 2]))
        out.append(ord(_B64[((b0 & 3) << 4) | (b1 >> 4)]))
        out.append(ord(_B64[((b1 & 15) << 2) | (b2 >> 6)]) if i+1 < n else 0x3D)
        out.append(ord(_B64[b2 & 63]) if i+2 < n else 0x3D)
        i += 3
    out.append(0x0A)
    return bytes(out)
def hexlify(data, sep=None):
    return bytes("".join("%02x" % b for b in data), "ascii")
def unhexlify(s):
    if isinstance(s, str): s = s.encode()
    return bytes(int(s[i:i+2], 16) for i in range(0, len(s), 2))
`;

const SAMPLE_SECRETS = `
secrets = {
    "ssid": "home-net",
    "password": "********",
    "timezone_offset": 5.5,
    "github_username": "swamstick911",
    "github_token": "ghp_sampletoken",
    "hackatime_api_key": "sample_key",
    "hackatime_uid": "U12345",
    "hackatime_username": "swamstick",
    "hackatime_projects": [["Shelby", "shelby"], ["Website", "website"]],
}
`;

// main.py, reshaped: setup runs once, the while-loop body becomes step()
const EMU_MAIN = `
import machine, time, gc, sys
from machine import Pin, SPI, WDT
import st7735
from src.font import FONT
import hwbridge

def _localtime(secs=None):
    return tuple(hwbridge.lt(i) for i in range(8))
time.localtime = _localtime
time.gmtime = _localtime
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(hwbridge.millis())
    time.ticks_diff = lambda a, b: a - b
    time.ticks_add = lambda a, b: a + b
# the wasm gc reports the browser heap; give the modules that display
# memory a device-like gc so they show ~264 KB like the real Sprig
import gc as _realgc
class _DevGC:
    def collect(self):
        try: _realgc.collect()
        except Exception: pass
    def mem_free(self): return 142 * 1024
    def mem_alloc(self): return 122 * 1024
_devgc = _DevGC()
for _name in ("system", "settings"):
    try:
        _m = __import__("src." + _name, None, None, [_name])
        _m.gc = _devgc
    except Exception as _e:
        print("gc patch skipped:", _name, _e)

# keep music from doing heavy per-sample DSP in the browser (UI still shows)
try:
    import src.music as _music
    _music.MusicScreen._play_tone = lambda self, *a, **k: 0.0
except Exception as _e:
    print("music patch skipped:", _e)

spi = SPI(0)
display = st7735.TFT(spi, 22, 26, 20)
display.initg(); display.rgb(False); display.rotation(1)
display.fill(st7735.TFT.BLACK)

BUTTON_W = Pin(5, Pin.IN, Pin.PULL_UP);  BUTTON_A = Pin(6, Pin.IN, Pin.PULL_UP)
BUTTON_S = Pin(7, Pin.IN, Pin.PULL_UP);  BUTTON_D = Pin(8, Pin.IN, Pin.PULL_UP)
BUTTON_I = Pin(12, Pin.IN, Pin.PULL_UP); BUTTON_J = Pin(13, Pin.IN, Pin.PULL_UP)
BUTTON_K = Pin(14, Pin.IN, Pin.PULL_UP); BUTTON_L = Pin(15, Pin.IN, Pin.PULL_UP)

class Button:
    def __init__(self, pin):
        self.pin = pin; self._last = True; self._pressed = False
    def update(self):
        val = self.pin.value()
        self._pressed = (self._last == True and val == False)
        self._last = val
    def pressed(self):
        return self._pressed

btns = {"W": Button(BUTTON_W), "A": Button(BUTTON_A), "S": Button(BUTTON_S), "D": Button(BUTTON_D),
        "I": Button(BUTTON_I), "J": Button(BUTTON_J), "K": Button(BUTTON_K), "L": Button(BUTTON_L)}

try:
    from secrets import secrets
except Exception:
    secrets = {}

wifi_connected = False
wifi_mgr = None
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
except Exception as e:
    print("WiFi error:", e); wifi_connected = False

from src.clock import ClockScreen
from src.menu import MenuScreen
clock = ClockScreen(display)
menu_scr = MenuScreen(display, FONT)
clock.show_menu_hint(0)
clock.update()

wdt = None
current_view = "Clock"
active_app = None
gh_count = 0

def load_app(module_name, class_name, *args):
    gc.collect()
    try:
        mod = __import__("src." + module_name, None, None, [class_name])
        app_class = getattr(mod, class_name)
        app = app_class(*args)
        app.show()
        return app
    except Exception as e:
        print("Failed to load", module_name, ":", e)
        return None

def unload_app():
    global active_app
    active_app = None
    gc.collect()

def step():
    global current_view, active_app
    for b in btns.values():
        b.update()
    if current_view == "Clock":
        clock.update()
    if btns["J"].pressed():
        if current_view == "Menu":
            current_view = "Clock"; clock.last_sec = -1; clock.needs_full_redraw = True
            clock.show_menu_hint(0, gh_count, 0); clock.update()
    if current_view == "Clock":
        if btns["L"].pressed():
            current_view = "Menu"; menu_scr.show()
    elif current_view == "Menu":
        result = menu_scr.handle_input(btns)
        if result == "github" and wifi_connected:
            current_view = "GitHub"; active_app = load_app("github", "GithubScreen", display, FONT, secrets, wdt)
        elif result == "system":
            current_view = "System"; active_app = load_app("system", "SystemScreen", display, FONT)
        elif result == "tasks":
            current_view = "Tasks"; active_app = load_app("tasks", "TaskScreen", display, FONT)
        elif result == "settings":
            current_view = "Settings"; active_app = load_app("settings", "SettingsScreen", display, FONT, secrets, wifi_mgr)
        elif result == "hackatime":
            current_view = "Hackatime"; active_app = load_app("hackatime", "HackatimeScreen", display, FONT, secrets, wdt)
        elif result == "music":
            current_view = "Music"; active_app = load_app("music", "MusicScreen", display, FONT, None)
        if result and current_view not in ["Clock", "Menu"] and active_app is None:
            current_view = "Menu"; menu_scr.show()
    elif active_app is not None:
        result = active_app.handle_input(btns)
        if result == "menu":
            if current_view == "Settings" and hasattr(active_app, "use_24h"):
                clock.use_24h = active_app.use_24h; clock.needs_full_redraw = True; clock.last_sec = -1
            unload_app(); current_view = "Menu"; menu_scr.show()

def show_screen(name):
    # render a single real app screen (used for the thumbnail tiles)
    try:
        if name == "clock":
            clock.needs_full_redraw = True; clock.last_sec = -1; clock.update()
        elif name == "menu":
            menu_scr.show()
        elif name == "github":
            from src.github import GithubScreen
            GithubScreen(display, FONT, secrets, None).show()
        elif name == "hackatime":
            from src.hackatime import HackatimeScreen
            HackatimeScreen(display, FONT, secrets, None).show()
        elif name == "tasks":
            from src.tasks import TaskScreen
            TaskScreen(display, FONT).show()
        elif name == "system":
            from src.system import SystemScreen
            SystemScreen(display, FONT).show()
        elif name == "settings":
            from src.settings import SettingsScreen
            SettingsScreen(display, FONT, secrets, wifi_mgr).show()
        elif name == "music":
            from src.music import MusicScreen
            MusicScreen(display, FONT, None).show()
    except Exception as e:
        print("show_screen error:", name, e)

print("Shelby emulator booted.")
`;

/* ---------------- the JS bridge + loader ---------------- */

export async function loadEmulator(targetCanvas) {
  // 160x128 offscreen the firmware draws into
  const screen = document.createElement("canvas");
  screen.width = 160; screen.height = 128;
  const ctx = screen.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, 160, 128);

  const cssCache = new Map();
  let bgr = false;          // the device runs display.rgb(False) => BGR panel
  const css565 = (c) => {
    let v = cssCache.get(c);
    if (v) return v;
    const r5 = (c >> 11) & 0x1f, g6 = (c >> 5) & 0x3f, b5 = c & 0x1f;
    let r = (r5 * 255 / 31) | 0, g = (g6 * 255 / 63) | 0, b = (b5 * 255 / 31) | 0;
    if (bgr) { const t = r; r = b; b = t; }   // match the real panel's colour order
    v = `rgb(${r},${g},${b})`;
    cssCache.set(c, v);
    return v;
  };

  // button pin state (PULL_UP: 1 = released, 0 = pressed)
  const KEY_PIN = { W: 5, A: 6, S: 7, D: 8, I: 12, J: 13, K: 14, L: 15 };
  const pins = {}; Object.values(KEY_PIN).forEach((p) => (pins[p] = 1));
  let freq = 250000000;

  const bridge = {
    px(x, y, c) { ctx.fillStyle = css565(c); ctx.fillRect(x, y, 1, 1); },
    fillrect(x, y, w, h, c) { ctx.fillStyle = css565(c); ctx.fillRect(x, y, w, h); },
    set_rgb(on) { bgr = !on; cssCache.clear(); },   // rgb(False) -> BGR colour order
    pin_get(id) { return pins[id] != null ? pins[id] : 1; },
    adc_read() { return 13900; },        // ~ room temperature on the Pico sensor
    get_freq() { return freq; },
    set_freq(f) { freq = f; },
    millis() { return performance.now() | 0; },
    lt(i) {
      const d = new Date();
      return [d.getFullYear(), d.getMonth() + 1, d.getDate(), d.getHours(),
              d.getMinutes(), d.getSeconds(), (d.getDay() + 6) % 7, 0][i];
    },
    http_sample(url, method) { return sampleFor(url); },
  };

  // sample API payloads shaped for the firmware's streaming parsers
  function sampleFor(url) {
    if (url.includes("graphql") || url.includes("github")) {
      let s = '{"data":{"user":{"contributionsCollection":{"contributionCalendar":{"weeks":[';
      const days = [];
      let seed = 7;
      for (let i = 0; i < 126; i++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        const r = seed % 100;
        const v = r < 45 ? 0 : r < 70 ? (seed % 3) : r < 88 ? 2 + (seed % 4) : 6 + (seed % 9);
        days.push('{"contributionCount":' + v + '}');
      }
      s += '{"contributionDays":[' + days.join(",") + ']}]}}}}}';
      return s;
    }
    if (url.includes("last_7_days")) {
      return '{"data":{"human_readable_total":"18 hrs 40 mins","status":"ok"}}';
    }
    if (url.includes("statusbar/today")) {
      return '{"data":{"grand_total":{"text":"3 hrs 12 mins"}},"text":"3 hrs 12 mins"}';
    }
    if (url.includes("/badge/")) {
      const t = url.includes("website") ? "4 hrs 02 mins" : "6 hrs 18 mins";
      return '<svg xmlns="http://www.w3.org/2000/svg"><g><text x="0" y="14">project</text>' +
             '<text x="60" y="14">hackatime: ' + t + '</text></g></svg>';
    }
    return "{}";
  }

  // load MicroPython
  const mod = await import(MP_URL);
  const mp = await mod.loadMicroPython();
  mp.registerJsModule("hwbridge", bridge);

  // mount real firmware files
  try { mp.FS.mkdir("/src"); } catch (e) {}
  for (const f of FW_FILES) {
    const res = await fetch("firmware/" + f);
    if (!res.ok) throw new Error("missing firmware file: " + f);
    let text = await res.text();
    // the wasm build has no native emitter; these decorators are speed hints
    // only, so strip them (behaviour is identical, just interpreted)
    if (f.endsWith(".py")) text = text.replace(/^[ \t]*@micropython\.(native|viper|asm_thumb)[^\n]*\r?\n/gm, "");
    mp.FS.writeFile("/" + f, text);
  }
  // write the shim modules + sample config
  const writes = {
    "/st7735.py": SHIM_ST7735, "/machine.py": SHIM_MACHINE, "/network.py": SHIM_NETWORK,
    "/socket.py": SHIM_SOCKET, "/urequests.py": SHIM_UREQUESTS, "/micropython.py": SHIM_MICROPYTHON,
    "/ujson.py": SHIM_UJSON, "/ubinascii.py": SHIM_UBINASCII, "/secrets.py": SAMPLE_SECRETS,
    "/emu_main.py": EMU_MAIN,
  };
  for (const [path, src] of Object.entries(writes)) mp.FS.writeFile(path, src);

  mp.runPython("import sys; sys.path.insert(0, '/')");
  mp.runPython(mp.FS.readFile("/emu_main.py", { encoding: "utf8" }));

  function step() { mp.runPython("step()"); }
  function showScreen(name) { mp.runPython("show_screen(" + JSON.stringify(name) + ")"); }
  function getView() { try { return mp.runPython("current_view"); } catch (e) { return null; } }
  // latch presses so a fast tap is held long enough for one loop step to see
  // the edge, while real holds (e.g. volume) still report as held
  const MIN_HOLD = 70;
  const downAt = {};
  function setKey(key, down) {
    const p = KEY_PIN[key.toUpperCase()];
    if (p == null) return;
    if (down) { pins[p] = 0; downAt[p] = performance.now(); }
    else {
      const held = performance.now() - (downAt[p] || 0);
      if (held < MIN_HOLD) setTimeout(() => { pins[p] = 1; }, MIN_HOLD - held);
      else pins[p] = 1;
    }
  }
  return { step, setKey, showScreen, getView, screen };
}
