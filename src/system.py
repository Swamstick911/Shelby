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