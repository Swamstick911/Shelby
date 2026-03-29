import time
from src.font import FONT

class ClockScreen:
    def __init__(self, display):
        self.display = display
        self.last_sec = -1
        self.last_min = -1
        self.width = 160
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
        rays= [(0,-10),(0,10),(10,0),(-10,0),(7,7),(-7,-7),(7,-7),(-7,7)]
        for dx, dy in rays:
            self._draw_pixel(cx + dx, cy + dy, orange)
            self._draw_pixel(cx + dx + 1, cy + dy, orange)

        #Sun core
        for x in range(-5, 6):
            for y in range(-5, 6):
                if x*x + y*y <= 25:
                    self._draw_pixel(cx + x, cy + y, yellow)
        
    def _draw_sky(self, hour, minute):
        is_day = 6 <= hour < 18

        #Setup background gradient colours
        if is_day:
            if hour < 9: bg = self._color(100, 180, 255) #Morning
            elif hour < 16: bg = self._color(40, 140, 255) #noon
            else: bg = self._color(200, 100, 50) #Sunset
        else:
            bg = self._color(0, 0, 40) #night

        self._fill_rect(0, 0, self.width, self.height, bg)

        #Physics: calculate the position across the 12 hour arc
        if is_day:
            mins_since_rise = (hour - 6) * 60 + minute
        else:
            mins_since_rise = ((hour + 6) % 24) * 60 + minute

        progress = mins_since_rise / 720.0
        cx = int(progress * 160)
        #Parabolic arc- peaks at y=8 in middle and drops to y=80 at edges
        cy = int(8 + ((cx - 80) ** 2) / 80)

        if is_day:
            self._draw_sun(cx, cy)
            #static cloud
            white = self._color(255, 255, 255)
            for c in [(30, 20), (120, 15), (70, 30)]:
                self._fill_rect(c[0], c[1], 15, 6, white)
                self._fill_rect(c[0]+3, c[1]-3, 9, 6, white)
        else:
            self._draw_moon(cx, cy)
            #static stars
            white = self._color(255, 255, 255)
            stars = [(20, 15),(40, 30), (80, 10), (130, 25), (150, 5), (90, 35)]
            for sx, sy in stars:
                self._draw_pixel(sx, sy, white)


    #Main loop
    def update(self):
        now = time.localtime()
        if now[5] == self.last_sec:
            return
        self.last_sec = now[5]
        
        hour = now[3]
        minute = now[4]
        
        # Redraw entire sky when the MINUTE changes to animate Sun/Moon movement
        if minute != self.last_min:
            self.last_min = minute
            self._draw_sky(hour, minute)
            
        is_day = 6 <= hour < 18
        text_bg = self._color(40, 140, 255) if is_day else self._color(0, 0, 40)
        if is_day and hour >= 16: text_bg = self._color(200, 100, 50)
        
        time_col = self._color(255, 255, 255)
        date_col = self._color(220, 255, 220) if is_day else self._color(180, 200, 255)
        stat_col = self._color(255, 255, 100)
        
        # Clear only the text boundaries to avoid flickering
        self._fill_rect(0, 45, self.width, 30, text_bg)
        self._fill_rect(0, 80, self.width, 18, text_bg)
        self._fill_rect(0, 115, self.width, 13, text_bg)
        
        # HUGE TIME (Scale 3 - 16px wide per char)
        hr_12 = hour % 12 or 12
        time_str = f"{hr_12}:{minute:02d}"
        time_w = len(time_str) * 16
        time_x = (self.width - time_w) // 2 - 8 # offset slightly left for AM/PM
        self._draw_text(time_str, time_x, 48, time_col, scale=3)
        
        # Small AM/PM indicator (Scale 1)
        ampm = "AM" if hour < 12 else "PM"
        self._draw_text(ampm, time_x + time_w + 2, 65, time_col, scale=1)
        
        # MEDIUM DATE (Scale 2 - 11px wide per char)
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        date_str = f"{months[now[1]-1]} {now[2]}"
        date_w = len(date_str) * 11
        date_x = (self.width - date_w) // 2
        self._draw_text(date_str, date_x, 82, date_col, scale=2)
        
        # Status Bar
        stat_w = len(self.status_text) * 6
        stat_x = (self.width - stat_w) // 2
        self._draw_text(self.status_text, stat_x, 118, stat_col, scale=1)

    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]
        
        if index == 0:
            badges = []
            if gh_count > 0: badges.append(f"GH:{gh_count}")
            if mail_count > 0: badges.append(f"Mail:{mail_count}")
            self.status_text = " | ".join(badges) if badges else "All caught up!"
        else:
            self.status_text = f"-> {menus[index]} (D)"
            
        hour = time.localtime()[3]
        is_day = 6 <= hour < 18
        text_bg = self._color(40, 140, 255) if is_day else self._color(0, 0, 40)
        if is_day and hour >= 16: text_bg = self._color(200, 100, 50)
        
        self._fill_rect(0, 115, self.width, 13, text_bg)
        stat_w = len(self.status_text) * 6
        stat_x = (self.width - stat_w) // 2
        self._draw_text(self.status_text, stat_x, 118, self._color(255, 255, 100), scale=1)