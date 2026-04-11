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
        self.use_24h = False
        self.weather = "CLEAR"
        self._last_weather = "CLEAR"
        self._particles = []
        self._last_anim_tick = time.ticks_ms()
        self._lightning_active = False

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
        w = self.weather
        if w in ("CLOUDY", "FOG", "STORM"):
            if 6 <= h < 18: return self._color(130, 140, 150)
            else: return self._color(15, 15, 30)
        if w in ("RAIN",):
            if 6<= h < 18: return self._color(80, 100, 120)
            else: return self._color(10, 10, 25)
        if w in "SNOW":
            if 6 <= h < 18: return self._color(190, 200, 215)
            else: return self._color(20, 20, 45)
        if 6 <= h < 18:
            if h < 9: return self._color(100, 180, 255)
            elif h < 16: return self._color(40, 140, 255)
            else: return self._color(200, 100, 50)
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

    def _draw_clouds(self, bg, thick=False):
        """Thick grey cloud bank for CLOUDY/STORM"""
        if thick:
            gc = self._color(140, 145, 150)
            dc = self._color(110, 115, 120)
            for cx, cy, w, h in [
                (0, 10, 60, 10), (50, 6, 70, 14), (110, 12, 50, 10),
                (20, 20, 50, 8), (80, 18, 55, 10)
            ]:
                self._fill_rect(cx, cy, w, h, gc)
                self._fill_rect(cx+4,cy-4, w-8, 6, dc)
        else:
            white = self._color(255, 235, 255)
            for c in [(30, 20), (120, 15), (70, 30)]:
                self._fill_rect(c[0], c[1], 15, 6, white)
                self._fill_rect(c[0]+3, c[1]-3, 9, 6, white)

    def _init_particles(self, count):
        """Seed rain or snow particles at pseudo random positions"""
        self._particles = []
        seed = time.localtime()[5] + 1
        for i in range(count):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            x = (seed % self.width)
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            y = (seed % (self.height - 25))
            speed = 2 if self.weather == "RAIN" else 1
            self._particles.append([x, y, speed])

    def _draw_rain(self, bg):
        """Draw and advance rain streaks"""
        blue = self._color(100, 150, 220)
        lblue = self._color(140, 190, 255)
        if not self._particles:
            self._init_particles(14)

        for p in self._particles:
            #erase old
            self._draw_pixel(p[0], p[1], bg)
            self._draw_pixel(p[0], p[1]+1, bg)
            self._draw_pixel(p[0], p[1]+2, bg)
            #advance
            p[1] += p[2]
            if p[1] >= self.height - 25:
                p[1] = 0
                p[0] = (p[0] * 1103515245 + 12345) & 0x7FFFFFFF
                p[0] = p[0] % self.width
            #draw new
            self._draw_pixel(p[0], p[1], lblue)
            self._draw_pixel(p[0], p[1]+1, blue)
            self._draw_pixel(p[0], p[1]+2, blue)
        
    def _draw_snow(self, bg):
        """Draw and advance snow flakes"""
        white = self._color(240, 245, 255)
        if not self._particles:
            self._init_particles(10)
        
        for p in self._particles:
            self._draw_pixel(p[0], p[1], bg)
            p[1] += 1
            #slight horizontal drift using motion
            drift = ((p[0] * 17 + p[1]) % 3) - 1
            p[0] = max(0, min(self.width-1, p[0] + drift))
            if p[1] >= self.height - 25:
                p[1] = 0
                p[0] = (p[0] * 1103515245 + 12345) & 0x7FFFFFFF
                p[0] = p[0] % self.width
            self._draw_pixel(p[0], p[1], white)

    def _draw_fog(self, bg):
        """Horizontal semi transparent fog bands"""
        fog = self._color(200, 205, 210)
        for y in range(8, 40, 6):
            self._fill_rect(0, y, self.width, 2, fog)

    def _draw_lightning(self, bg):
        """Draws a zigzag flash"""
        flash = self._color(255, 255, 180)
        pts = [(80,5),(75,15),(82,15),(72,30),(85,30),(70,45)]
        for i in range(len(pts) - 1):
            x1,y1  = pts[i]; x2,y2 = pts[i+1]
            steps = max(abs(x2-x1), abs(y2-y1))
            if steps:
                for s in range(steps):
                    xi = x1 + (x2-x1)*s//steps
                    yi = y1 + (y2-y1)*s//steps
                    self._draw_pixel(xi, yi, flash)

    def _repaint_all(self, hour, minute, now):
        h = int(hour)
        is_day = 6 <= h < 18
        bg = self._sky_bg(hour)
        w = self.weather

        # fill ENTIRE screen with sky color
        self._fill_rect(0, 0, self.width, self.height, bg)

        # celestial arc
        mins = (h - 6) * 60 + minute if is_day else ((h + 6) % 24) * 60 + minute
        progress = mins / 720.0
        cx = int(progress * 160)
        cy = int(8 + ((cx - 80) ** 2) / 80)

        # Draw sun/moon and static weather elements based on condition
        if w == "CLEAR":
            if is_day:
                self._draw_sun(cx, cy)
                self._draw_clouds(bg, thick=False)
            else:
                self._draw_moon(cx, cy)
                white = self._color(255, 255, 255)
                for sx, sy in [(20,15),(40,30),(80,10),(130,25),(150,5),(90,35)]:
                    self._draw_pixel(sx, sy, white)

        elif w == "CLOUDY":
            if is_day: self._draw_sun(cx, cy)
            else:      self._draw_moon(cx, cy)
            self._draw_clouds(bg, thick=True)

        elif w == "STORM":
            self._draw_clouds(bg, thick=True)

        elif w == "FOG":
            if is_day: self._draw_sun(cx, cy)
            else:      self._draw_moon(cx, cy)
            self._draw_fog(bg)

        elif w == "RAIN":
            self._draw_clouds(bg, thick=True)
            if not self._particles:
                self._init_particles(14)

        elif w == "SNOW":
            self._draw_clouds(bg, thick=False)
            if not self._particles:
                self._init_particles(10)

        # draw ALL text on top
        time_col = self._color(255, 255, 255)
        date_col = self._color(220, 255, 220) if is_day else self._color(180, 200, 255)

        if self.use_24h:
            time_str = f"{hour:02d}:{minute:02d}"
            time_w = len(time_str) * 16
            time_x = (self.width - time_w) // 2
            self._draw_text(time_str, time_x, 48, time_col, scale=3)
        else:
            hr_12 = hour % 12 or 12
            time_str = f"{hr_12}:{minute:02d}"
            time_w = len(time_str) * 16
            time_x = (self.width - time_w) // 2 - 8
            self._draw_text(time_str, time_x, 48, time_col, scale=3)
            ampm = "AM" if hour < 12 else "PM"
            self._draw_text_on_bg(ampm, time_x + time_w + 2, 60, time_col, bg)

        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        date_str = f"{months[now[1]-1]} {now[2]}"
        date_w = len(date_str) * 11
        date_x = (self.width - date_w) // 2
        self._draw_text(date_str, date_x, 82, date_col, scale=2)

        # Weather label bottom-left
        if w != "CLEAR":
            label_map = {
                "CLOUDY": "Cloudy", "RAIN": "Rain", "SNOW": "Snow",
                "STORM": "Storm",  "FOG":  "Fog"
            }
            wlabel = label_map.get(w, "")
            self._draw_text(wlabel, 3, 112, self._color(200, 220, 255), scale=1)

        # draw status bar
        stat_col = self._color(255, 255, 100)
        stat_w = len(self.status_text) * 6
        stat_x = (self.width - stat_w) // 2
        self._draw_text_on_bg(self.status_text, stat_x, 112, stat_col, bg)
        self.prev_status_text = self.status_text

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
        now    = time.localtime()
        sec    = now[5]
        hour   = now[3]
        minute = now[4]
        w      = self.weather

        # 1. Handle Weather Condition Changes
        if self._last_weather != w:
            self._particles = []
            self._last_weather = w
            self.needs_full_redraw = True

        # 2. Clear lightning leftovers from previous second
        if self._lightning_active and sec % 7 != 0:
            self.needs_full_redraw = True
            self._lightning_active = False

        # 3. Particle Animation Engine (runs ~10 FPS decoupled from seconds)
        anim_tick = False
        current_ms = time.ticks_ms()
        if time.ticks_diff(current_ms, self._last_anim_tick) > 100:
            self._last_anim_tick = current_ms
            anim_tick = True

        if sec == self.last_sec and not self.needs_full_redraw:
            # Advance particles smoothly between full second ticks
            if anim_tick and w in ("RAIN", "SNOW") and self._particles:
                bg = self._sky_bg(hour)
                if w == "RAIN":  self._draw_rain(bg)
                elif w == "SNOW": self._draw_snow(bg)
            return

        self.last_sec = sec

        # 4. Handle Redraws
        if minute != self.prev_minute or self.needs_full_redraw:
            self.prev_minute = minute
            self._repaint_all(hour, minute, now)
            self.needs_full_redraw = False
        else:
            # Same minute, different second -> handle per-second logic (like lightning)
            if w == "STORM" and sec % 7 == 0:
                self._draw_lightning()
                self._lightning_active = True
                
            # If a second ticked but particles didn't get their anim_tick yet, force draw them so they don't skip
            if w in ("RAIN", "SNOW") and self._particles:
                bg = self._sky_bg(hour)
                if w == "RAIN":   self._draw_rain(bg)
                elif w == "SNOW": self._draw_snow(bg)

    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]
        if index == 0:
            badges = []
            if gh_count > 0: badges.append(f"GH:{gh_count}")
            if mail_count > 0: badges.append(f"Mail:{mail_count}")
            self.status_text = " | ".join(badges) if badges else "All caught up!"
        else:
            self.status_text = f"-> {menus[index]} (D)"

        self.needs_full_redraw = True
        self.last_sec = -1

    def _draw_char_on_bg(self, ch, x, y, fg, bg):
        #draw a single character with explicit background color at scale=1
        ci = ord(ch)
        if not (FONT["Start"] <= ci <= FONT["End"]):
            return
        fontw = FONT["Width"]
        fonth = FONT["Height"]
        ci = (ci - FONT["Start"]) * fontw
        charA = FONT["Data"][ci:ci + fontw]

        for col in range(fontw):
            c = charA[col]
            for row in range(fonth):
                color = fg if (c & 0x01) else bg
                self._draw_pixel(x + col, y + row, color)
                c >>= 1

    def _draw_text_on_bg(self, text, x, y, fg, bg):
        """Draw text with explicit background color at scale=1"""
        px = x
        for ch in text:
            self._draw_char_on_bg(ch, px, y, fg, bg)
            px += FONT["Width"] + 1