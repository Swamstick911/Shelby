import time
import st7735
from src.font import FONT

C = st7735.TFT.color

#Colors
_BG = C(8, 12, 24)
_HEADER = C(36, 41, 46) #Github dark header
_ACCENT = C(88, 166, 255) #Github blue
_WHITE = C(240, 240, 240)
_GRAY = C(110, 118, 125)
_YELLOW = C(210, 153, 34) # unread dot
_GREEN = C(63, 185, 119)
_RED = C(248, 81, 73)
_ROWSEL = C(22, 27, 34) # selected row bg

W = 160
H = 128
CHAR_W = 6
CHAR_H = 8
ROW_H = 11
MAX_ROWS = 5
HEADER_H = 14
FOOTER_H = 10

def _tw(s, scale=1):
    return len(s) * CHAR_W * scale

def _cx(s, scale=1):
    return(W - _tw(s, scale)) // 2


class GitHubScreen:
    def __init__(self, display, secrets):
        self.display = display
        self.token = secrets.get("github_token", "")
        self.notifs = [] # list of ("repo", "title", etc)
        self.unread = 0
        self.cursor = 0
        self.scroll = 0
        self.status = "I=refresh"
        self.fetched = False
        self._last_fetch = 0
        
    # Public API

    def draw(self):
        self._fill(0, 0, W, H, _BG)
        self._draw_header()
        self._draw_body()
        self._draw_footer()

    def update(self):
        # Auto refresh every 5 minutes after first manual fetch
        if self.fetched and time.ticks_diff(time.ticks_ms(), self._last_fetch) > 300_000:
            self.fetch()

    def on_button(self, btn):
        if btn == "W":
            if self.cursor > 0:
                self.cursor -= 1
                if self.cursor < self.scroll:
                    self.scroll = self.cursor
                self._draw_body()
        elif btn == "S":
            if self.cursor < len(self.notifs) - 1:
                self.cursor += 1
                if self.cursor >= self.scroll + MAX_ROWS:
                    self.scroll += 1
                self._draw_body()
        elif btn == "I":
            self.fetch()
        elif btn == "K":
            if self.notifs:
                n = self.notifs[self.cursor]
                n["unread"] = not n["unread"]
                self.unread = sum(1 for x in self.notifs if x["unread"])
                self._draw_header()
                self._draw_body()

        
    def fetch(self):
        self.status = "Fetching..."
        self._draw_footer()
        try:
            import urequests
            headers = {
                "Authorisation": "Bearer " + self.token,
                "User-Agent": "Shelby-Sprig",
                "Accept": "application/vnd.github.v3+json",
            }
            r = urequests.get(
                "https://api.github.com/notifications?per_page=20&all=false",
                headers=headers,
                timeout = 10
            )
            code = r.status_code
            if code == 200:
                import ujson
                data = ujson.loads (r.text)
                r.close()
                self.notifs = []
                for n in data:
                    self.notifs.append({
                        "repo": n["repository"]["name"][:20],
                        "title": n["subject"]["title"][:26],
                        "type": n["subject"]["type"],
                        "unread": n["unread"],
                    })
                self.unread = sum(1 for x in self.notifs if x["unread"])
                self.status = "{} notif, {} unread".format(len(self.notifs), self.unread)
                self.fetched = True
            elif code == 304:
                r.close()
                self.status = "No changes"
            else:
                r.close()
                self.status = "HTTP {}".format(code)
        except MemmoryError:
            self.status = "Out of memory!"
        except Exception as e:
            self.status = str(e)[:22]
        self.cursor = 0
        self.scroll = 0
        self._last_fetch = time.ticks_ms()
        self.draw()

    # Draw helpers

    def _draw_header(self):
        self._fill(0, 0, W, HEADER_H, _HEADER)
        title = "GitHub"
        badge = str(self.unread)
        self._text(title, 4, 3, _WHITE)
        #Unread badge on the right
        bx = W - len(badge) * CHAR_W - 6
        self._fill(bx - 2, 2, len(badge) * CHAR_W + 6, 10, _YELLOW)
        self._text(badge, bx, 3, _BG)

    def _draw_body(self):
        y0 = HEADER_H
        body_h = H - HEADER_H - FOOTER_H
        self._fill(0, y0, W, body_h, _BG)

        if not self.notifs:
            msg = "No notifications"
            self._text(msg, _cx(msg), y0 + body_h // 2 - 4, _GRAY)
            return
        
        visible = self.notifs[self.scroll : self.scroll + MAX_ROWS]
        y = y0 + 1
        for i, n in enumerate(visible):
            real_i = i + self.scroll
            is_sel = (real_i == self.cursor)
            row_bg = _ROWSEL if is_sel else _BG
            self._fill(0, y, W, ROW_H, row_bg)

            #unread dot
            dot_c = _YELLOW if n["unread"] else _BG
            self._fill(2, y + 3, 3, 3, dot_c)

            #Repo + title
            repo_str = n["repo"][:14]
            title_str = m["title"][:(W // CHAR_W - 2)]
            label_color = _WHITE if n["unread"] else _GRAY
            self._text(repo_str + ":", 7, y + 1, _ACCENT)
            used = len(repo_str) + 1
            remaining = (W - 7) // CHAR_W - used - 1
            if remaining > 0:
                self._text(n["title"][:remaining], 7 + used * CHAR_W, y + 1, label_color)
                y += ROW_H

        #Scroll bar
        if len(self.notifs) > MAX_ROWS:
            sb_h = body_h * MAX_ROWS // len(self.notifs)
            sb_y = y0 + (body_h * self.scroll) // len(self.notifs)
            self._fill(W - 2, y0, 2, body_h, _HEADER)
            self._fill(W - 2, sb_y, 2, sb_h, _ACCENT)

    def _draw_footer(self):
        self._fill(0, H - FOOTER_H, W, FOOTER_H, _HEADER)
        s = self.status[:26]
        self._text(s, 2, H - FOOTER_H + 1, _GRAY)

    def _text(self, s, x, y, color):
        self.display.text((x, y), s, color, FONT, 1)

    def _fill(self, x, y, w, h, color):
        self.display.fillrect((x, y), (w, h), color)