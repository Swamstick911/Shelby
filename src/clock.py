import time

# Minimal 5x8 built-in font (ASCII 32-127), compatible with boochow ST7735 driver
# Each character is 5 columns of 8-bit column data (LSB = top row)
_FONT_DATA = (
    b'\x00\x00\x00\x00\x00'  # 32 space
    b'\x00\x00\x5f\x00\x00'  # 33 !
    b'\x00\x07\x00\x07\x00'  # 34 "
    b'\x14\x7f\x14\x7f\x14'  # 35 #
    b'\x24\x2a\x7f\x2a\x12'  # 36 $
    b'\x23\x13\x08\x64\x62'  # 37 %
    b'\x36\x49\x55\x22\x50'  # 38 &
    b'\x00\x05\x03\x00\x00'  # 39 '
    b'\x00\x1c\x22\x41\x00'  # 40 (
    b'\x00\x41\x22\x1c\x00'  # 41 )
    b'\x14\x08\x3e\x08\x14'  # 42 *
    b'\x08\x08\x3e\x08\x08'  # 43 +
    b'\x00\x50\x30\x00\x00'  # 44 ,
    b'\x08\x08\x08\x08\x08'  # 45 -
    b'\x00\x60\x60\x00\x00'  # 46 .
    b'\x20\x10\x08\x04\x02'  # 47 /
    b'\x3e\x51\x49\x45\x3e'  # 48 0
    b'\x00\x42\x7f\x40\x00'  # 49 1
    b'\x42\x61\x51\x49\x46'  # 50 2
    b'\x21\x41\x45\x4b\x31'  # 51 3
    b'\x18\x14\x12\x7f\x10'  # 52 4
    b'\x27\x45\x45\x45\x39'  # 53 5
    b'\x3c\x4a\x49\x49\x30'  # 54 6
    b'\x01\x71\x09\x05\x03'  # 55 7
    b'\x36\x49\x49\x49\x36'  # 56 8
    b'\x06\x49\x49\x29\x1e'  # 57 9
    b'\x00\x36\x36\x00\x00'  # 58 :
    b'\x00\x56\x36\x00\x00'  # 59 ;
    b'\x08\x14\x22\x41\x00'  # 60 <
    b'\x14\x14\x14\x14\x14'  # 61 =
    b'\x00\x41\x22\x14\x08'  # 62 >
    b'\x02\x01\x51\x09\x06'  # 63 ?
    b'\x32\x49\x79\x41\x3e'  # 64 @
    b'\x7e\x11\x11\x11\x7e'  # 65 A
    b'\x7f\x49\x49\x49\x36'  # 66 B
    b'\x3e\x41\x41\x41\x22'  # 67 C
    b'\x7f\x41\x41\x22\x1c'  # 68 D
    b'\x7f\x49\x49\x49\x41'  # 69 E
    b'\x7f\x09\x09\x09\x01'  # 70 F
    b'\x3e\x41\x49\x49\x7a'  # 71 G
    b'\x7f\x08\x08\x08\x7f'  # 72 H
    b'\x00\x41\x7f\x41\x00'  # 73 I
    b'\x20\x40\x41\x3f\x01'  # 74 J
    b'\x7f\x08\x14\x22\x41'  # 75 K
    b'\x7f\x40\x40\x40\x40'  # 76 L
    b'\x7f\x02\x04\x02\x7f'  # 77 M
    b'\x7f\x04\x08\x10\x7f'  # 78 N
    b'\x3e\x41\x41\x41\x3e'  # 79 O
    b'\x7f\x09\x09\x09\x06'  # 80 P
    b'\x3e\x41\x51\x21\x5e'  # 81 Q
    b'\x7f\x09\x19\x29\x46'  # 82 R
    b'\x46\x49\x49\x49\x31'  # 83 S
    b'\x01\x01\x7f\x01\x01'  # 84 T
    b'\x3f\x40\x40\x40\x3f'  # 85 U
    b'\x1f\x20\x40\x20\x1f'  # 86 V
    b'\x3f\x40\x38\x40\x3f'  # 87 W
    b'\x63\x14\x08\x14\x63'  # 88 X
    b'\x07\x08\x70\x08\x07'  # 89 Y
    b'\x61\x51\x49\x45\x43'  # 90 Z
    b'\x00\x7f\x41\x41\x00'  # 91 [
    b'\x02\x04\x08\x10\x20'  # 92 backslash
    b'\x00\x41\x41\x7f\x00'  # 93 ]
    b'\x04\x02\x01\x02\x04'  # 94 ^
    b'\x40\x40\x40\x40\x40'  # 95 _
    b'\x00\x01\x02\x04\x00'  # 96 `
    b'\x20\x54\x54\x54\x78'  # 97 a
    b'\x7f\x48\x44\x44\x38'  # 98 b
    b'\x38\x44\x44\x44\x20'  # 99 c
    b'\x38\x44\x44\x48\x7f'  # 100 d
    b'\x38\x54\x54\x54\x18'  # 101 e
    b'\x08\x7e\x09\x01\x02'  # 102 f
    b'\x0c\x52\x52\x52\x3e'  # 103 g
    b'\x7f\x08\x04\x04\x78'  # 104 h
    b'\x00\x44\x7d\x40\x00'  # 105 i
    b'\x20\x40\x44\x3d\x00'  # 106 j
    b'\x7f\x10\x28\x44\x00'  # 107 k
    b'\x00\x41\x7f\x40\x00'  # 108 l
    b'\x7c\x04\x18\x04\x78'  # 109 m
    b'\x7c\x08\x04\x04\x78'  # 110 n
    b'\x38\x44\x44\x44\x38'  # 111 o
    b'\x7c\x14\x14\x14\x08'  # 112 p
    b'\x08\x14\x14\x18\x7c'  # 113 q
    b'\x7c\x08\x04\x04\x08'  # 114 r
    b'\x48\x54\x54\x54\x20'  # 115 s
    b'\x04\x3f\x44\x40\x20'  # 116 t
    b'\x3c\x40\x40\x20\x7c'  # 117 u
    b'\x1c\x20\x40\x20\x1c'  # 118 v
    b'\x3c\x40\x30\x40\x3c'  # 119 w
    b'\x44\x28\x10\x28\x44'  # 120 x
    b'\x0c\x50\x50\x50\x3c'  # 121 y
    b'\x44\x64\x54\x4c\x44'  # 122 z
    b'\x00\x08\x36\x41\x00'  # 123 {
    b'\x00\x00\x7f\x00\x00'  # 124 |
    b'\x00\x41\x36\x08\x00'  # 125 }
    b'\x10\x08\x08\x10\x08'  # 126 ~
    b'\x00\x00\x00\x00\x00'  # 127 DEL
)

FONT = {
    'Start': 32,
    'End': 127,
    'Width': 5,
    'Height': 8,
    'Data': _FONT_DATA
}

class ClockScreen:
    def __init__(self, display):
        self.display = display
        self.last_sec = -1
        self._last_hour = -1
        self.width = 160
        self.height = 128
        self.status_text = "All caught up!"

    # Color helper

    def _color(self, r, g, b):
        # Converting RGB888 to RGB565 for ST7735
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    # Pixel art drawing

    def _draw_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.display.pixel((x, y), color)

    def _fill_rect(self, x, y, w, h, color):
        self.display.fillrect((x, y), (w, h), color)

    # Added FONT parameter to the raw boochow call
    def _draw_text(self, text, x, y, color, scale=1):
        self.display.text((x, y), text, color, FONT, scale)

    def _draw_star(self, x, y, color):
        self._draw_pixel(x,     y,     color)
        self._draw_pixel(x - 1, y,     color)
        self._draw_pixel(x + 1, y,     color)
        self._draw_pixel(x,     y - 1, color)
        self._draw_pixel(x,     y + 1, color)

    def _draw_moon(self, x, y):
        yellow = self._color(255, 255, 0)
        glow   = self._color(255, 255, 180)
        grey   = self._color(180, 180, 180)
        bg     = self._color(0, 0, 34)

        moon_pixels = [
            (1,0),(2,0),(3,0),
            (0,1),(1,1),(2,1),(3,1),(4,1),
            (0,2),(1,2),(2,2),(3,2),(4,2),
            (0,3),(1,3),(2,3),(3,3),(4,3),
            (1,4),(2,4),(3,4),
        ]
        for dx, dy in moon_pixels:
            self._draw_pixel(x+dx, y+dy, yellow)

        # Carve out crescent moon
        shadow = [
            (2,0),(3,0),
            (2,1),(3,1),(4,1),
            (2,2),(3,2),(4,2),
            (2,3),(3,3),(4,3),
            (2,4),(3,4),
        ]
        for dx, dy in shadow:
            self._draw_pixel(x+dx, y+dy, bg)

        # Craters
        self._draw_pixel(x+1, y+2, grey)
        self._draw_pixel(x+0, y+3, grey)

        # Glow
        glow_pixels = [
            (0,-1),(1,-1),(2,-1),(-1,0),(-1,1),(-1,2),
            (0,5),(1,5),(2,5),(5,1),(5,2),(5,3)
        ]
        for dx, dy in glow_pixels:
            self._draw_pixel(x+dx, y+dy, glow)

    def _draw_night_scene(self):
        white = self._color(255, 255, 255)
        warm  = self._color(255, 255, 150)
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
        warm_stars = [(65,12),(140,22),(90,8)]

        for sx, sy in big_stars:
            self._draw_star(sx, sy, white)
        for sx, sy in small_stars:
            self._draw_pixel(sx, sy, white)
        for sx, sy in warm_stars:
            self._draw_pixel(sx, sy, warm)

    def _draw_morning_scene(self):
        orange = self._color(255, 136, 0)
        warm   = self._color(255, 220, 68)
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
            (0,-7),(1,-7),(-1,-7),
            (-5,-5),(-4,-5),(4,-5),(5,-5),
            (-7,0),(-7,1),(7,0),(7,1),
            (-5,5),(-4,5),(4,5),(5,5),
            (0,7),(1,7),(-1,7),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x+dx, sun_y+dy, warm)

        for ax, ay in [(20,10),(45,18),(70,8),(95,22)]:
            self._draw_pixel(ax, ay, accent)

    def _draw_afternoon_scene(self):
        orange = self._color(255, 136, 0)
        white  = self._color(255, 255, 255)
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
        warm   = self._color(255, 220, 68)
        pink   = self._color(255, 170, 170)
        sun_x, sun_y = 140, 100

        for i in range(0, 25, 3):
            self._draw_pixel(sun_x-i, sun_y,   orange)
            self._draw_pixel(sun_x-i, sun_y-1, orange)
        for i in range(0, 20, 3):
            self._draw_pixel(sun_x-i, sun_y-4, pink)
            self._draw_pixel(sun_x-i, sun_y-6, pink)

        sun_body = [
            (-3,-3),(-2,-3),(-1,-3),(0,-3),(1,-3),(2,-3),(3,-3),
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

    # Main update

    def update(self):
        now = time.localtime()

        if now[5] == self.last_sec:
            return
        self.last_sec = now[5]

        hour = now[3]

        # Redraw background art only when the hour changes
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

        # Pick colors based on time of day
        if 6 <= hour < 12:
            text_bg  = self._color(220, 100, 0)
            time_col = self._color(255, 255, 255)
            date_col = self._color(255, 238, 204)
            stat_col = self._color(255, 255, 150)
        elif 12 <= hour < 18:
            text_bg  = self._color(0, 100, 200)
            time_col = self._color(255, 255, 255)
            date_col = self._color(220, 240, 255)
            stat_col = self._color(255, 255, 150)
        elif 18 <= hour < 21:
            text_bg  = self._color(120, 30, 0)
            time_col = self._color(255, 238, 170)
            date_col = self._color(255, 204, 170)
            stat_col = self._color(255, 200, 100)
        else:
            text_bg  = self._color(0, 0, 34)
            time_col = self._color(200, 220, 255)
            date_col = self._color(170, 187, 221)
            stat_col = self._color(150, 200, 255)

        # Clear just the text rows so pixel art stays intact
        self._fill_rect(0,  45, self.width, 14, text_bg)
        self._fill_rect(0,  68, self.width, 10, text_bg)
        self._fill_rect(0, 118, self.width, 10, text_bg)

        # Time string - centered
        hr_12    = hour % 12 or 12
        ampm     = "AM" if hour < 12 else "PM"
        time_str = f"{hr_12:02d}:{now[4]:02d} {ampm}"
        time_x   = (self.width - len(time_str) * 8) // 2
        # Pass FONT explicitly
        self.display.text((time_x, 46), time_str, time_col, FONT, 1)

        # Date string - centered
        months   = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
        date_str = f"{months[now[1]-1]} {now[2]:02d}, {now[0]}"
        date_x   = (self.width - len(date_str) * 8) // 2
        # Pass FONT explicitly
        self.display.text((date_x, 69), date_str, date_col, FONT, 1)

        # Status bar at the bottom
        stat_x = (self.width - len(self.status_text) * 8) // 2
        # Pass FONT explicitly
        self.display.text((stat_x, 119), self.status_text, stat_col, FONT, 1)

    # Menu hint

    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]

        if index == 0:
            badges = []
            if gh_count > 0:
                badges.append(f"GH:{gh_count}")
            if mail_count > 0:
                badges.append(f"Mail:{mail_count}")
            self.status_text = " | ".join(badges) if badges else "All caught up!"
        else:
            self.status_text = f"-> {menus[index]} (D)"

        # Redraw status bar immediately without waiting for next second tick
        hour = time.localtime()[3]
        if 6 <= hour < 12:
            stat_col = self._color(255, 255, 150)
            text_bg  = self._color(220, 100, 0)
        elif 12 <= hour < 18:
            stat_col = self._color(255, 255, 150)
            text_bg  = self._color(0, 100, 200)
        elif 18 <= hour < 21:
            stat_col = self._color(255, 200, 100)
            text_bg  = self._color(120, 30, 0)
        else:
            stat_col = self._color(150, 200, 255)
            text_bg  = self._color(0, 0, 34)

        self._fill_rect(0, 118, self.width, 10, text_bg)
        stat_x = (self.width - len(self.status_text) * 8) // 2
        # Pass FONT explicitly
        self.display.text((stat_x, 119), self.status_text, stat_col, FONT, 1)