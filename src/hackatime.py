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
PURPLE = _c(180, 100, 255)

def _fmt_seconds(seconds):
    """Convert seconds to hours and minutes"""
    if seconds is None:
        return "No data"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return "{}h {}m".format(h, m)
    return "{}m".format(m)

class HackatimeScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.today = None
        self.week = None
        self.streak = None
        self.project = None
        self.proj_sec = None
        self.error = None

    def show(self):
        d = self.display
        d.fill(BG)
        #Title bar
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Hackatime", WHITE, self.font, 1)
        d.text((110, 3), "J:back", GREY, self.font, 1)
        d.text((45, 55), "Loading...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        gc.collect()
        import ubinascii

        key     = self.secrets.get("hackatime_api_key", "")
        encoded = ubinascii.b2a_base64(key.encode()).decode().strip()
        headers = {
            "Authorization": "Basic " + encoded,
            "Accept":        "application/json"
        }

        try:
            r = urequests.get(
                "https://hackatime.hackclub.com/api/hackatime/v1/users/current/stats/last_7_days",
                headers=headers
            )
            if r.status_code == 200:
                data = r.json().get("data", {})

                # Week total
                self.week = data.get("total_seconds", 0)

                # Today — last item in days array
                days = data.get("days", [])
                if days:
                    self.today = days[-1].get("total_seconds", 0)
                else:
                    self.today = 0

                # Streak — from the days array, count consecutive days with > 0
                streak = 0
                for day in reversed(days):
                    if day.get("total_seconds", 0) > 0:
                        streak += 1
                    else:
                        break
                self.streak = streak

                # Top project
                projects = data.get("projects", [])
                if projects:
                    top           = projects[0]
                    self.project  = top.get("name", "")[:14]
                    self.proj_sec = top.get("total_seconds", 0)

                self.error = None
            else:
                self.error = "HTTP " + str(r.status_code)
            r.close()

        except Exception as e:
            self.error = str(e)[:22]
            print("Hackatime error:", e)

        gc.collect()
    
    def _draw(self):
        d = self.display
        d.fillrect((0, 16), (160, 100), BG)

        if self.error:
            d.text((8, 50), "Error: ", RED, self.font, 1)
            d.text((8, 62), self.error, RED, self.font, 1)
            return
        
        y = 20
        
        #Today
        d.text((8, y), "Today", GREY, self.font, 1)
        y += 12
        today_str = _fmt_seconds(self.today)
        d.text((8, y), today_str, CYAN, self.font, 2)
        y += 20

        #divider
        d.line((8, y), (152, y), GREY)
        y += 4

        #This week
        d.text((8, y), "This week", GREY, self.font, 1)
        y += 12
        week_str = _fmt_seconds(self.week)
        d.text((8, y), week_str, CYAN, self.font, 2)
        y += 20

        #Divider
        d.line((8, y), (152, y), GREY)
        y += 4

        #Streak
        streak_str = (str(self.streak) + "d streak") if self.streak else "No streak"
        d.text((8, y), streak_str, PURPLE, self.font, 1)

        if self.project:
            proj_str = self.project
            px = 158 - len(proj_str) * 6
            d.text((px, y), proj_str, GREEN, self.font, 1)

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        if btns["K"].pressed():
            #Manual refresh
            self.show()
        return None