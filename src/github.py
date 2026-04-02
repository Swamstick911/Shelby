import st7735
import urequests
import gc

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED
CYAN = st7735.TFT.CYAN
GREY = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)

class GithubScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.notifs = []
        self.error = None

    def show(self):
        """Fetch notifications and render"""
        d = self.display
        d.fill(BG)
        #title bar
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "GitHub", WHITE, self.font, 1)
        d.text((110, 3), "A:back", GREY, self.font, 1)
        d.text((60, 55), "Loading...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        gc.collect()
        try:
            headers = {
                "Authorization": "Bearer " + self.secrets.get("github_token", ""),
                "User-Agent": "Sprig-Shelby"
            }
            r = urequests.get(
                "https://api.github.com/notifications?per_page=5",
                headers=headers
            )
            if r.status_code == 200:
                data = r.json()
                self.notifs = []
                for n in data:
                    title = n.get("subject", {}).get("title", "Unknown")
                    if len(title) > 22:
                        title = title[:21] + "~"
                    self.notifs.append(title)
                self.error = None
            else:
                self.error = "HTTP" + str(r.status_code)
            r.close()
        except Exception as e:
            self.error = str(e)[:22]
        gc.collect()

    def _draw(self):
        d = self.display
        d.fillrect((0, 16), (160, 112), BG)

        if self.error:
            d.text((8, 50), "Error:", RED, self.font, 1)
            d.text((8, 62), self.error, RED, self.font, 1)
            return

        if not self.notifs:
            d.text((20, 55), "All caught up!", GREEN, self.font, 1)
            return
        
        #count badge
        count = str(len(self.notifs)) + " notification" + ("s" if len(self.notifs) != 1 else "")
        d.text((8, 18), count, CYAN, self.font, 1)

        #List notifications
        y = 30
        for i, title in enumerate(self.notifs):
            color = WHITE if i % 2 == 0 else GREY
            d.text((8, y), title, color, self.font, 1)
            y += 14
            if y > 110:
                break

    def handle_input(self, btns):
        """Returns 'menu' when A is pressed, otherwise None"""
        if btns["A"].pressed():
            return "menu"
        return None
    