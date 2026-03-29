import time
from src.font import FONT


class ClockScreen:
    def __init__(self, display):
        self.display = display
        self.last_sec = -1
        self.prev_minute = -1
        self.width = 160
        self.height = 128
        self.status_text = "All caught up!"
        self.prev_status_text = ""
        self.needs_full_redraw = True

    def _color(self, r, g, b):
        return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)

    def _draw_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.display.pixel((x, y), color)

    def _fill_rect(self, x, y, w, h, color):
        self.display.fillrect((x, y), (w, h), color)

    def _draw_text(self, text, x, y, color, scale=1):
        self.display.text((x, y), text, color, FONT, scale)

    def _sky_bg(self, hour):
        h = int(hour)
        if 6 <= h < 18:
            if h < 9:  return self._color(100, 180, 255)
            elif h < 16: return self._color(40, 140, 255)
            else:        return self._color(200, 100, 50)
        else:
            return self._color(0, 0, 40)

    def _draw_moon(self, cx, cy):
        yellow = self._color(255, 255, 100)
        bg = self._color(0, 0, 40)
        for x in range(-6, 7):
            for y in range(-6, 7):
                if x*x + y*y <= 36:
                    self._draw_pixel(cx+x, cy+y, yellow)
        for x in range(-6, 7):
            for y in range(-6, 7):
                if (x-3)**2 + (y-2)**2 <= 36:
                    self._draw_pixel(cx+x, cy+y, bg)

    def _draw_sun(self, cx, cy):
        orange = self._color(255, 150, 0)
        yellow = self._color(255, 220, 0)
        for dx, dy in [(0,-10),(0,10),(10,0),(-10,0),(7,7),(-7,-7),(7,-7),(-7,7)]:
            self._draw_pixel(cx+dx, cy+dy, orange)
            self._draw_pixel(cx+dx+1, cy+dy, orange)
        for x in range(-5, 6):
            for y in range(-5, 6):
                if x*x + y*y <= 25:
                    self._draw_pixel(cx+x, cy+y, yellow)

    def _repaint_all(self, hour, minute, now):
        h = int(hour)
        is_day = 6 <= h < 18
        bg = self._sky_bg(hour)

        # Step 1: fill ENTIRE screen with sky color
        # This means text will always sit on the correct background - no patches possible
        self._fill_rect(0, 0, self.width, self.height, bg)

        # Step 2: draw sky elements (sun/moon/clouds/stars)
        mins = (h - 6) * 60 + minute if is_day else ((h + 6) % 24) * 60 + minute
        progress = mins / 720.0
        cx = int(progress * 160)
        cy = int(8 + ((cx - 80) ** 2) / 80)

        if is_day:
            self._draw_sun(cx, cy)
            white = self._color(255, 255, 255)
            for c in [(30, 20), (120, 15), (70, 30)]:
                self._fill_rect(c[0], c[1], 15, 6, white)
                self._fill_rect(c[0]+3, c[1]-3, 9, 6, white)
        else:
            self._draw_moon(cx, cy)
            white = self._color(255, 255, 255)
            for sx, sy in [(20,15),(40,30),(80,10),(130,25),(150,5),(90,35)]:
                self._draw_pixel(sx, sy, white)

        # Step 3: draw ALL text on top (background is already the sky color)
        time_col = self._color(255, 255, 255)
        date_col = self._color(220, 255, 220) if is_day else self._color(180, 200, 255)

        hr_12 = hour % 12 or 12
        time_str = f"{hr_12}:{minute:02d}"
        time_w = len(time_str) * 16
        time_x = (self.width - time_w) // 2 - 8
        self._draw_text(time_str, time_x, 48, time_col, scale=3)

        ampm = "AM" if hour < 12 else "PM"
        self._draw_text(ampm, time_x + time_w + 2, 65, time_col, scale=1)

        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        date_str = f"{months[now[1]-1]} {now[2]}"
        date_w = len(date_str) * 11
        date_x = (self.width - date_w) // 2
        self._draw_text(date_str, date_x, 82, date_col, scale=2)

        # Step 4: draw status bar
        self._draw_status(hour)

    def _draw_status(self, hour):
        # Clear just status row with exact sky color, then draw text
        bg = self._sky_bg(hour)
        self._fill_rect(0, 115, self.width, 13, bg)
        stat_col = self._color(255, 255, 100)
        stat_w = len(self.status_text) * 6
        stat_x = (self.width - stat_w) // 2
        self._draw_text(self.status_text, stat_x, 118, stat_col, scale=1)
        self.prev_status_text = self.status_text

    def update(self):
        now = time.localtime()
        sec = now[5]
        hour = now[3]
        minute = now[4]

        if sec == self.last_sec and not self.needs_full_redraw:
            return
        self.last_sec = sec

        # Full repaint only when minute changes or forced
        if minute != self.prev_minute or self.needs_full_redraw:
            self.prev_minute = minute
            self._repaint_all(hour, minute, now)
            self.needs_full_redraw = False

        # Status bar update between minute changes
        elif self.status_text != self.prev_status_text:
            self._draw_status(hour)

    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]
        if index == 0:
            badges = []
            if gh_count > 0: badges.append(f"GH:{gh_count}")
            if mail_count > 0: badges.append(f"Mail:{mail_count}")
            self.status_text = " | ".join(badges) if badges else "All caught up!"
        else:
            self.status_text = f"-> {menus[index]} (D)"