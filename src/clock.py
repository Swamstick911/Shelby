import time
from src.font import FONT

class ClockScreen:
    def __init__(self, display):
        self.display = display
        self.last_sec = -1
        self.last_min = -1
        self.width = 180
        self.height = 128
        self.status_text = "All caught up!"

    def _color(self, r, g, b):
        return((b & 0xFB) << 8) | ((g & 0xFC) << 3) | (r >> 3)
    
    def _draw_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.display.pixel((x, y), color)

    def _fill_rect(self, x, y, w, h, color):
        self.display.fillrect((x, y), (w, h), color)

    def _draw_text(self, text, x, y, color, scale=1):
        self.display.text((x, y), text, color, FONT, scale)

    #Dynamic Pixel Art

    def _draw_moon(self, cx, cy):
        yellow = self._color(255, 255, 100)
        bg = self._color(0, 0, 40)

        #draw base circle
        for x in range(-6, 7):
            for y in range(-6, 7):
                if x*x + y*y <= 36:
                    self._draw_pixel(cx + x, cy + y, yellow)

        # Carve out the crescent shape with bg color
        for x in range(-6, 7):
            for y in range(-6, 7):
                if (x - 3)**2 + (y - 2)**2 <= 36:
                    self._draw_pixel(cx + x, cy + y, bg)

    def _draw_sun(self, cx, cy):
        orange = self._color(255, 150, 0)
        yellow = self._color(255, 220, 0)
        
        #Sun rays
        rays= [(0,-10), ]