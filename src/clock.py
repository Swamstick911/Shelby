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

    def _draw_pixel(self, x, y, art, color):
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

    def _draw_night_scene(self):
        white = self._color(255, 255, 255)
        warm = self._color(255, 255, 150)
        self._draw_moon(10, 8)

        big_stars = [
            (50,6),(80,12),(110,5),(135,15),
            (145,8),(30,18),(95,20),(60,25),
        ]
        small_stars = [
            (40,10),(70,8),(100,15),(120,10),
            (155,20),(25,14),(88,22),(115,25),
            (42,28),(130,6),(75,30),(55,15),
            (148,25),(35,30),(105,28),
        ]
        warm_stars = [ (65,12),(140,22),(90,8) ]

        for sx, sy in big_stars:
            self._draw_star(sx, sy, white)
        for sx, sy in small_stars:
            self._draw_pixel(sx, sy, white)
        for sx, sy in warm_stars:
            self._draw_pixel(sx, sy, warm)

    def _draw_morning_scene(self):
        orange = self._color(255, 136, 0)
        warm = self._color(255, 220, 68)
        accent = self._color(170, 221, 255)
        sun_x, sun_y = 130, 95

        rays = [
            (0,-12),(0,-14),(8,-9),(10,-11),
            (12,0),(14,0),(8,9),(10,11),
            (-8,-9),(-10,-11),(-12,0),(-14,0),        
        ]
        for dx, dy in rays:
            self._draw_pixel(sun_x+dx, sun_y+dy, orange)

        sun_body = [
            (0,-7),(1,-7),(-1.-7),
            (-5,-5),(-4,-5),(4,-5),(5,-5),
            (-7,0),(-7,1),(7,0),(7,1),
            (-5,5),(-4,5),(4,5),(5,5),
            (0,7),(1,7),(-1,7),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x+dx, sun_y+dy, warm)

        for ax, ay in [(20,0),(45,18),(70,8),(95,22)]:
            self._draw_pixel(ax, ay, accent)
    
    def _draw_afternoon_scene(self):
        orange = self._color(255, 136, 0)
        white = self._color(255, 255, 255)
        sun_x, sun_y = 130, 20

        rays = [
            (0,-10),(0,-12),(7,-7),(9,-9),
            (10,0),(12,0),(7,7),(9,9),
            (0,10),(0,12),(-7,7),(-9,9),
            (-10,0),(-12,0),(-7,-7),(-9,-9),
        ]
        for dx, dy in rays:
            self._draw_pixel(sun_x+dx, sun_y+dy, orange)

        sun_body = [
            (-1,-6),(0,-6),(1,-6),
            (-4,-4),(-3,-4),(3,-4),(4,-4),
            (-6,-1),(-6,0),(6,-1),(6,0),
            (-4,4),(-3,4),(3,4),(4,4),
            (-1,6),(0,6),(1,6),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x+dx, sun_y+dy, white)

    def _draw_evening_scene(self):
        orange = self._color(255, 136, 0)
        warm = self._color(255, 220, 68)
        pink = self._color(255, 170, 170)
        sun_x, sun_y = 140, 100

        for i in range(0, 25, 3):
            self._draw_pixel(sun_x-i, sun_y, orange)
            self._draw_pixel(sun_x-i, sun_y-1, orange)
        for i in range(0, 20, 3):
            self._draw_pixel(sun_x-i, sun_y-4, pink)
            self._draw_pixel(sun_x-i, sun_y-6, pink)

        sun_body = [
            (-3,-3),(-3,-3),(-1,-3),(0,-3),(1,-3),(2,-3),(3,-3),
            (-5,-2),(-4,-2),(4,-2),(5,-2),
            (-6,-1),(-5,-1),(5,-1),(6,-1),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x+dx, sun_y+dy, warm)

        clouds = [
            (30,20),(31,20),(32,20),(33,20),(34,20),
            (29,21),(30,21),(31,21),(32,21),(33,21),(34,21),(35,21),
            (60,30),(61,30),(62,30),(63,30),
            (59,31),(60,31),(61,31),(62,31),(63,31),(64,31),
        ]
        for cx, cy in clouds:
            self._draw_pixel(cx, cy, pink)

        #Text Drawing
        def _draw_text(self, text, x, y, color, scale=1):
            self.display.text(text, x, y, color)

        #Main update
        def update(self):
            now = time.localtime()

            if now[5] == self.last_sec:
                return
            self.last_sec = now[5]

            hour = now[3]

            #Redraw background when hour changes
            if hour != self._last_hour:
                self._last_hour = hour

                if 6 <= hour < 12:
                    bg = self._color(220, 100, 0)
                    self._fill_rect(0, 0, self.width, self.height, bg)
                    self._draw_morning_scene()

                elif 12 <= hour < 18:
                    bg = self._color(0, 100, 200)
                    self._fill_rect(0, 0, self.width, self.height, bg)
                    self._draw_afternoon_scene()

                elif 18 <= hour < 21:
                    bg = self._color(120, 30, 0)
                    self._fill_rect(0, 0, self.width, self.height, bg)
                    self._draw_evening_scene()

                else:
                    bg = self._color(0, 0, 34)
                    self._fill_rect(0, 0, self.width, self.height, bg)
                    self._draw_night_scene()
            
            #Time String
            hr_12 = hour % 12 or 12
            ampm = "AM" if hour < 12 else "PM"
            time_str = f"{hr_12:02d}:{now[4]:02d} {ampm}"

            #Clear text area befpre redrawing
            if 6 <= hour < 12:
                text_bg = self._color(220, 100, 0)
                time_col = self.color(255, 255, 255)
                date_col = self._color(255, 238, 204)
            elif 12 <= hour < 18:
                text_bg = self._color(0, 100, 200)
                time_col = self.color(255, 255, 255)
                date_col = self._color(255, 240, 255)
            elif 18 <= hour < 21:
                text_bg = self._color(120, 30, 0)
                time_col = self.color(255, 238, 170)
                date_col = self._color(255, 204, 170)
            else:
                text_bg = self._color(0, 0, 34)
                time_col = self.color(200, 220,255)
                date_col = self._color(170, 200, 255)
                