# src/github.py
import st7735
import urequests
import gc
from src.utils import draw_text_on_bg


def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BG       = st7735.TFT.BLACK
WHITE    = st7735.TFT.WHITE
GREEN    = st7735.TFT.GREEN
RED      = st7735.TFT.RED
CYAN     = st7735.TFT.CYAN
GREY     = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)


class GithubScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font    = font
        self.secrets = secrets
        self.notifs  = []
        self.error   = None

    def show(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        draw_text_on_bg(d, self.font, "GitHub", 8,   3, WHITE, TITLE_BG)
        draw_text_on_bg(d, self.font, "A:back",  110, 3, GREY,  TITLE_BG)
        d.text((60, 55), "Loading...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        import gc
        gc.collect()
        try:
            import urequests
            headers = {
                "Authorization": "Bearer " + self.secrets.get("github_token", ""),
                "User-Agent": "Sprig-Shelby"
            }
            r = urequests.get(
                "https://api.github.com/notifications?per_page=3",
                headers=headers,
                stream=True
            )
            if r.status_code == 200:
                self.notifs = []
                buf = ""
                while len(self.notifs) < 3:
                    chunk = r.raw.read(128)  # <-- Changed this line
                    if not chunk:
                        break
                    buf += chunk.decode("utf-8", "ignore")
                    
                    idx = buf.find('"title":')
                    if idx != -1:
                        start = buf.find('"', idx + 8) + 1
                        if start > 0:
                            end = buf.find('"', start)
                            if end != -1:
                                title = buf[start:end]
                                if len(title) > 22:
                                    title = title[:21] + "~"
                                self.notifs.append(title)
                                buf = buf[end:]
                    elif len(buf) > 256:
                        buf = buf[-128:]
                self.error = None
            else:
                self.error = "HTTP " + str(r.status_code)
            r.close()
        except Exception as e:
            self.error = str(e)[:22]
        gc.collect()

    def _draw(self):
        d = self.display
        d.fillrect((0, 16), (160, 100), BG)

        if self.error:
            d.text((8, 50), "Error:", RED, self.font, 1)
            d.text((8, 62), self.error, RED, self.font, 1)
            return

        if not self.notifs:
            d.text((20, 55), "All caught up!", GREEN, self.font, 1)
            return

        #Count badge
        count = str(len(self.notifs)) + " notif" + ("s" if len(self.notifs) != 1 else "")
        d.text((8, 18), count, CYAN, self.font, 1)

        #Notification list
        y = 30
        for i, title in enumerate(self.notifs):
            color = WHITE if i % 2 == 0 else GREY
            d.text((8, y), title, color, self.font, 1)
            y += 14
            if y > 110:
                break

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        if btns["K"].pressed():
            self.show()
        return None