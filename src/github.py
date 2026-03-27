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