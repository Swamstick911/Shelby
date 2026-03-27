import time
import framebuf

class ClockScreen:
    def __init__(self, display):
        self.display = display
        self.last_sec = -1
        self._last_hour = -1
        self.width = 160
        self.height = 128

    #Color helpers

    def _color(self, r, g, b):
        #Converting RGB888 to RBG565 for ST7735
        return((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        
        #Pixel art drawing

    def _draw_pixel_art(self, x, y, art, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.display.pixel(x, y, color)

    def _fill_rect(self, x, y, w, h, color):
        self.display.fill_rect(x, y, w, h, color)

    def _draw_star(self, x, y, color):
        self._draw_pixel(x,     y,      color)
        self._draw_pixel(x - 1, y,      color)
        self._draw_pixel(x + 1, y,      color)
        self._draw_pixel(x,     y - 1,  color)
        self._draw_pixel(x,     y + 1,  color)

    def _draw_moon(self, x, y):
        yellow = self.color(255, 255, 0)
        glow = self.color(255, 255, 180)
        grey = self.color(180, 180, 180)
        bg = self._color(0, 0, 34)

 
        moon_pixels = [
            (1,0), (2,0), (3,0),
            (0,1), (1,1), (2,1), (3,1), (4,1),
            (0,2), (1,2), (2,2), (3,2), (4,2),
            (0,3), (1,3), (2,3), (3,3), (4,3),
            (1,4), (2,4), (3,4),
        ]
        for dx, dy in moon_pixels:
            self._draw_pixel(x+dx, y+dy, yellow)

        #carve out crescent moon
        shadow = [
            (2,0), (3,0),
            (2,1), (3,1), (4,1),
            (2,2), (3,2), (4,2),
            (2,3), (3,3), (4,3),
            (2,4), (3,4),
        ]
        for dx, dy in shadow:
            self._draw_pixel(x+dx, y+dy, bg)

        #Craters
        self._draw_pixel(x+1, y+2, grey)
        self._draw_pixel(x+0, y+3, grey)

        #Glow
        glow_pixels = [
            (0,-1),(1,-1),(2,-1),(-1,0),(-1,1),(-1,2),
            (0,5),(1,5),(2,5),(5,1),(5,2),(5,3)
        ]
        for dx, dy in glow_pixels:
            self._draw_pixel(x+dx, y+dy, glow)

    