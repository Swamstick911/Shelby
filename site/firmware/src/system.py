import st7735
import time
import gc
import machine
import network
from src.utils import draw_text_on_bg

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
TITLE_BG = _c(20, 80, 150)
GREEN = st7735.TFT.GREEN
CYAN = st7735.TFT.CYAN
GREY = _c(120, 120, 120)

class SystemScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.last_update = 0
        self.sensor_temp = machine.ADC(4)
        self.conversion_factor = 3.3 / 65535
        self.wlan = network.WLAN(network.STA_IF)

    def show(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        draw_text_on_bg(d, self.font, "System Monitor", 8, 3, WHITE, TITLE_BG)
        draw_text_on_bg(d, self.font, "J:back", 115, 3, GREY, TITLE_BG)

        self._update_stats()
    
    def _update_stats(self):
        d = self.display
        free = gc.mem_free()
        alloc = gc.mem_alloc()
        total = free + alloc
        ram_percent = int((alloc / total) * 100)

        reading = self.sensor_temp.read_u16() * self.conversion_factor
        temp_c = 27 - (reading - 0.706) / 0.001721

        rssi = self.wlan.status('rssi') if self.wlan.isconnected() else 0

        draw_text_on_bg(d, self.font, "Memory (RAM)", 8, 25, GREY, BG)
        d.fillrect((8, 38), (144, 12), BG)
        draw_text_on_bg(d, self.font, f"{alloc//1024}KB / {total//1024}KB", 8, 38, CYAN, BG)
        draw_text_on_bg(d, self.font, f"{ram_percent}%", 125, 38, GREEN, BG)

        draw_text_on_bg(d, self.font, "CPU Temp", 8, 60, GREY, BG)
        d.fillrect((8, 73), (144, 12), BG)
        draw_text_on_bg(d, self.font, f"{temp_c:.1f} C", 8, 73, CYAN, BG)

        draw_text_on_bg(d, self.font, "WiFi Signal", 8, 95, GREY, BG)
        d.fillrect((8, 108), (144, 12), BG)
        draw_text_on_bg(d, self.font, f"{rssi} dBm", 8, 108, CYAN, BG)

        self.last_update = time.ticks_ms()

    def handle_input(self, btns):
        #Update live stats every 2 seconds
        if time.ticks_diff(time.ticks_ms(), self.last_update) > 2000:
            self._update_stats()

        if btns["J"].pressed():
            return "menu"

        return None 