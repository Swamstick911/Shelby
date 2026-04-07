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
YELLOW = _c(255, 220, 0)
GREY = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)


def _parse_badge(text):
    """Extract time from <title>hackatime: 23h 56m</title>"""
    try:
        start = text.find("<title>")
        if start == -1:
            return "-"
        start += 7  # len("<title>")
        end = text.find("</title>", start)
        value = text[start:end]  # "hackatime: 23h 56m"
        colon = value.find(": ")
        if colon != -1:
            return value[colon + 2:]  # "23h 56m"
    except:
        pass
    return "-"


class HackatimeScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.stats = []
        self.error = None

    def show(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Hackatime", WHITE, self.font, 1)
        d.text((110, 3), "J:back", GREY,  self.font, 1)
        d.text((40, 55), "Loading...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        gc.collect()
        self.stats = []
        self.error = None

        uid = self.secrets.get("hackatime_uid", "")
        username = self.secrets.get("hackatime_username", "")
        projects = self.secrets.get("hackatime_projects", [])

        if not uid or not username or not projects:
            self.error = "No config"
            return

        base = "https://hackatime.hackclub.com/api/v1/badge/"

        for label, slug in projects:
            gc.collect()
            try:
                r = urequests.get(base + uid + "/" + username + "/" + slug)

                # urequests doesn't follow 307 redirects — do it manually
                if r.status_code in (301, 302, 307, 308):
                    location = r.headers.get("Location") or r.headers.get("location", "")
                    r.close()
                    gc.collect()
                    if location:
                        r = urequests.get(location)
                    else:
                        self.stats.append((label, "-"))
                        continue

                if r.status_code == 200:
                    raw = r.text
                    print("RAW:", raw[:300])
                    time_str = _parse_badge(raw)
                    print("PARSED:", time_str)
                else:
                    time_str = "err"
                r.close()
                self.stats.append((label, time_str))

            except Exception as e:
                print("Badge fetch error:", e)
                self.stats.append((label, "-"))
            gc.collect()

    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3),   "Hackatime", WHITE, self.font, 1)
        d.text((110, 3), "J:back", GREY,  self.font, 1)

        if self.error:
            d.text((8, 40), "Error:", RED,  self.font, 1)
            d.text((8, 52), self.error, GREY, self.font, 1)
            return

        if not self.stats:
            d.text((8, 55), "No data", GREY, self.font, 1)
            return

        d.text((8, 17),   "Project", CYAN, self.font, 1)
        d.text((110, 17), "Time", CYAN, self.font, 1)
        d.line((8, 27), (152, 27), GREY)

        y = 31
        for label, time_str in self.stats:
            d.text((8, y), label[:14], WHITE, self.font, 1)
            d.text((110, y), time_str[:10], YELLOW, self.font, 1)
            y += 13
            if y > 118:
                break

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        if btns["K"].pressed():
            self.show()
        return None