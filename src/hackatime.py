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
        start += 7
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
        self.today = "-"
        self.week = "-"
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
        self.today = "-"
        self.week  = "-"

        uid = self.secrets.get("hackatime_uid", "")
        username = self.secrets.get("hackatime_username", "")
        projects = self.secrets.get("hackatime_projects", [])
        api_key = self.secrets.get("hackatime_api_key", "")

        #Today and week via API
        if api_key:
            import ubinascii, time
            gc.collect()
            encoded = ubinascii.b2a_base64(api_key.encode()).decode().strip()
            headers = {"Authorization": "Basic " + encoded, "Accept": "application/json"}
            base_api = "https://hackatime.hackclub.com"
            try:
                r = urequests.get(
                    base_api + "/api/hackatime/v1/users/current/stats/last_7_days",
                    headers=headers
                )
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    self.week = data.get("human_readable_total", "-")
                r.close()
                gc.collect()
                time.sleep_ms(300)
                r2 = urequests.get(
                    base_api + "/api/hackatime/v1/users/current/statusbar/today",
                    headers=headers
                )
                if r2.status_code == 200:
                    td = r2.json().get("data", {}).get("grand_total", {})
                    self.today = td.get("text", "-")
                r2.close()
                gc.collect()
            except Exception as e:
                print("Stats fetch error:", e)
                gc.collect()

        #Per-project via badges (no auth needed)
        if not uid or not username or not projects:
            return
        base_badge = "https://hackatime.hackclub.com/api/v1/badge/"
        for label, slug in projects:
            gc.collect()
            try:
                r = urequests.get(base_badge + uid + "/" + username + "/" + slug)
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
                    time_str = _parse_badge(r.text)
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
        d.text((110, 3), "J:back",    GREY,  self.font, 1)

        if self.error:
            d.text((8, 40), "Error:",   RED,  self.font, 1)
            d.text((8, 52), self.error, GREY, self.font, 1)
            return

        #Today
        d.text((8, 16), "Today", GREY, self.font, 1)
        d.text((8, 26), self.today, CYAN, self.font, 2)

        #Divider
        d.line((8, 46), (152, 46), GREY)

        #7 days
        d.text((8, 50), "Last 7 days", GREY, self.font, 1)
        d.text((8, 60), self.week, CYAN, self.font, 2)

        #Divider
        d.line((8, 80), (152, 80), GREY)

        #Projects (2 max)
        y = 84
        for label, time_str in self.stats[:2]:
            d.text((8, y),   label[:12],    WHITE,  self.font, 1)
            d.text((100, y), time_str[:10], YELLOW, self.font, 1)
            y += 13


    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        if btns["K"].pressed():
            #Manual refresh
            self.show()
        return None