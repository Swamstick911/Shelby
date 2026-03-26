# src/clock.py
import time
import displayio
import terminalio
from adafruit_display_text import label

class ClockScreen(displayio.Group):
    def __init__(self, display_width=160, display_height=128):
        super().__init__()
        self.width = display_width
        self.height = display_height
        self._last_hour = -1

        # 1. Background color layer
        self.bg_bitmap = displayio.Bitmap(self.width, self.height, 1)
        self.bg_palette = displayio.Palette(1)
        self.bg_palette[0] = 0x000022
        self.bg_sprite = displayio.TileGrid(self.bg_bitmap, pixel_shader=self.bg_palette)
        self.append(self.bg_sprite)

        # 2. Pixel art layer for stars, moon, sun etc
        self.art_bitmap = displayio.Bitmap(self.width, self.height, 16)
        self.art_palette = displayio.Palette(16)
        self.art_palette.make_transparent(0)
        self.art_palette[1] = 0xFFFFFF  # white - stars, sun core
        self.art_palette[2] = 0xFFFF00  # yellow - moon, sun glow
        self.art_palette[3] = 0xFF8800  # orange - rays
        self.art_palette[4] = 0xFFDD44  # warm yellow - sun body
        self.art_palette[5] = 0xAADDFF  # light blue - morning accent
        self.art_palette[6] = 0xFFAAAA  # pink - sunset clouds
        self.art_palette[7] = 0xFFFFAA  # pale yellow - moon glow
        self.art_palette[8] = 0xCCCCCC  # grey - moon craters
        self.art_sprite = displayio.TileGrid(self.art_bitmap, pixel_shader=self.art_palette)
        self.append(self.art_sprite)

        # 3. Time label
        self.time_label = label.Label(
            terminalio.FONT,
            text="00:00 AM",
            color=0xFFFFFF,
            scale=3
        )
        self.time_label.anchor_point = (0.5, 0.5)
        self.time_label.anchored_position = (self.width // 2, self.height // 2 - 10)
        self.append(self.time_label)

        # 4. Date label
        self.date_label = label.Label(
            terminalio.FONT,
            text="Jan 01, 2000",
            color=0xDDDDDD,
            scale=1
        )
        self.date_label.anchor_point = (0.5, 0.5)
        self.date_label.anchored_position = (self.width // 2, self.height // 2 + 20)
        self.append(self.date_label)

        # 5. Status bar
        self.status_label = label.Label(
            terminalio.FONT,
            text="Loading...",
            color=0xFFFF00,
            scale=1
        )
        self.status_label.anchor_point = (0.5, 1.0)
        self.status_label.anchored_position = (self.width // 2, self.height - 4)
        self.append(self.status_label)

        self.last_update_sec = -1

    # ------------------------------------------------------------------ #
    # Pixel art helpers                                                    #
    # ------------------------------------------------------------------ #

    def _clear_art(self):
        for x in range(self.width):
            for y in range(self.height):
                self.art_bitmap[x, y] = 0

    def _draw_pixel(self, x, y, color_idx):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.art_bitmap[x, y] = color_idx

    def _draw_star(self, x, y, color_idx=1):
        self._draw_pixel(x,     y,     color_idx)
        self._draw_pixel(x - 1, y,     color_idx)
        self._draw_pixel(x + 1, y,     color_idx)
        self._draw_pixel(x,     y - 1, color_idx)
        self._draw_pixel(x,     y + 1, color_idx)

    def _draw_tiny_star(self, x, y, color_idx=1):
        self._draw_pixel(x, y, color_idx)

    def _draw_moon(self, x, y):
        moon_pixels = [
            (1,0),(2,0),(3,0),
            (0,1),(1,1),(2,1),(3,1),(4,1),
            (0,2),(1,2),(2,2),(3,2),(4,2),
            (0,3),(1,3),(2,3),(3,3),(4,3),
            (1,4),(2,4),(3,4),
        ]
        for dx, dy in moon_pixels:
            self._draw_pixel(x + dx, y + dy, 2)

        # Cut out the crescent shape
        shadow_pixels = [
            (2,0),(3,0),
            (2,1),(3,1),(4,1),
            (2,2),(3,2),(4,2),
            (2,3),(3,3),(4,3),
            (2,4),(3,4),
        ]
        for dx, dy in shadow_pixels:
            self._draw_pixel(x + dx, y + dy, 0)

        # Craters
        self._draw_pixel(x + 1, y + 2, 8)
        self._draw_pixel(x + 0, y + 3, 8)

        # Soft glow
        glow = [
            (0,-1),(1,-1),(2,-1),(-1,0),(-1,1),(-1,2),
            (0,5),(1,5),(2,5),(5,1),(5,2),(5,3)
        ]
        for dx, dy in glow:
            self._draw_pixel(x + dx, y + dy, 7)

    def _draw_night_scene(self):
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
            self._draw_star(sx, sy, 1)
        for sx, sy in small_stars:
            self._draw_tiny_star(sx, sy, 1)
        for sx, sy in warm_stars:
            self._draw_tiny_star(sx, sy, 2)

    def _draw_morning_scene(self):
        sun_x, sun_y = 130, 95
        rays = [
            (0,-12),(0,-14),(8,-9),(10,-11),
            (12,0),(14,0),(8,9),(10,11),
            (-8,-9),(-10,-11),(-12,0),(-14,0),
        ]
        for dx, dy in rays:
            self._draw_pixel(sun_x + dx, sun_y + dy, 3)

        sun_body = [
            (0,-7),(1,-7),(-1,-7),
            (-5,-5),(-4,-5),(4,-5),(5,-5),
            (-7,0),(-7,1),(7,0),(7,1),
            (-5,5),(-4,5),(4,5),(5,5),
            (0,7),(1,7),(-1,7),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x + dx, sun_y + dy, 4)

        accents = [(20,10),(45,18),(70,8),(95,22)]
        for ax, ay in accents:
            self._draw_tiny_star(ax, ay, 5)

    def _draw_afternoon_scene(self):
        sun_x, sun_y = 130, 20
        rays = [
            (0,-10),(0,-12),(7,-7),(9,-9),
            (10,0),(12,0),(7,7),(9,9),
            (0,10),(0,12),(-7,7),(-9,9),
            (-10,0),(-12,0),(-7,-7),(-9,-9),
        ]
        for dx, dy in rays:
            self._draw_pixel(sun_x + dx, sun_y + dy, 3)

        sun_body = [
            (-1,-6),(0,-6),(1,-6),
            (-4,-4),(-3,-4),(3,-4),(4,-4),
            (-6,-1),(-6,0),(6,-1),(6,0),
            (-4,4),(-3,4),(3,4),(4,4),
            (-1,6),(0,6),(1,6),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x + dx, sun_y + dy, 1)

    def _draw_evening_scene(self):
        sun_x, sun_y = 140, 100
        for i in range(0, 25, 3):
            self._draw_pixel(sun_x - i, sun_y, 3)
            self._draw_pixel(sun_x - i, sun_y - 1, 3)
        for i in range(0, 20, 3):
            self._draw_pixel(sun_x - i, sun_y - 4, 6)
            self._draw_pixel(sun_x - i, sun_y - 6, 6)

        sun_body = [
            (-3,-3),(-2,-3),(-1,-3),(0,-3),(1,-3),(2,-3),(3,-3),
            (-5,-2),(-4,-2),(4,-2),(5,-2),
            (-6,-1),(-5,-1),(5,-1),(6,-1),
            (-6,0),(-5,0),(5,0),(6,0),
        ]
        for dx, dy in sun_body:
            self._draw_pixel(sun_x + dx, sun_y + dy, 4)

        clouds = [
            (30,20),(31,20),(32,20),(33,20),(34,20),
            (29,21),(30,21),(31,21),(32,21),(33,21),(34,21),(35,21),
            (60,30),(61,30),(62,30),(63,30),
            (59,31),(60,31),(61,31),(62,31),(63,31),(64,31),
            (90,15),(91,15),(92,15),(93,15),
            (89,16),(90,16),(91,16),(92,16),(93,16),(94,16),
        ]
        for cx, cy in clouds:
            self._draw_pixel(cx, cy, 6)

    # ------------------------------------------------------------------ #
    # Main update — called every loop in code.py                          #
    # ------------------------------------------------------------------ #

    def update(self):
        now = time.localtime()

        if now.tm_sec == self.last_update_sec:
            return
        self.last_update_sec = now.tm_sec

        hour = now.tm_hour

        # Only redo the art layer when the hour actually changes
        if hour != self._last_hour:
            self._last_hour = hour

            if 6 <= hour < 12:       # Morning
                self.bg_palette[0] = 0xFF7700
                self.time_label.color = 0xFFFFFF
                self.date_label.color = 0xFFEECC
                self._clear_art()
                self._draw_morning_scene()

            elif 12 <= hour < 18:    # Afternoon
                self.bg_palette[0] = 0x0077CC
                self.time_label.color = 0xFFFFFF
                self.date_label.color = 0xEEFFFF
                self._clear_art()
                self._draw_afternoon_scene()

            elif 18 <= hour < 21:    # Evening
                self.bg_palette[0] = 0x882200
                self.time_label.color = 0xFFEEAA
                self.date_label.color = 0xFFCCAA
                self._clear_art()
                self._draw_evening_scene()

            else:                    # Night
                self.bg_palette[0] = 0x000022
                self.time_label.color = 0xCCDDFF
                self.date_label.color = 0xAABBDD
                self._clear_art()
                self._draw_night_scene()

        # Update time text every second
        ampm = "AM"
        hr_12 = hour
        if hour >= 12:
            ampm = "PM"
            if hour > 12:
                hr_12 = hour - 12
        if hr_12 == 0:
            hr_12 = 12

        self.time_label.text = f"{hr_12:02d}:{now.tm_min:02d} {ampm}"

        months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]
        month_str = months[now.tm_mon - 1] if 1 <= now.tm_mon <= 12 else "???"
        self.date_label.text = f"{month_str} {now.tm_mday:02d}, {now.tm_year}"

    # ------------------------------------------------------------------ #
    # Menu hint shown at the bottom of the clock screen                   #
    # ------------------------------------------------------------------ #

    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]

        if index == 0:
            badges = []
            if gh_count > 0:
                badges.append(f"GH:{gh_count}")
            if mail_count > 0:
                badges.append(f"Mail:{mail_count}")

            if len(badges) > 0:
                self.status_label.text = " | ".join(badges)
                self.status_label.color = 0xFFFF00
            else:
                self.status_label.text = "All caught up!"
                self.status_label.color = 0x00FF00
        else:
            self.status_label.text = f"-> {menus[index]} (D)"
            self.status_label.color = 0xFFFFFF