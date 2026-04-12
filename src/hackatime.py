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

class HackatimeScreen:
    def __init__(self, display, font, secrets, wdt=None):  # <--- Accept wdt
        self.display = display
        self.font = font
        self.secrets = secrets
        self.wdt = wdt                                     # <--- Store it
        self.stats = []
        self.today = "-"
        self.week = "-"
        self.error = None

    def show(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Hackatime", WHITE, self.font, 1)
        d.text((110, 3), "J:back", GREY, self.font, 1)
        d.text((40, 55), "Loading...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        gc.collect()
        self.stats = []
        self.error = None
        self.today = "-"
        self.week = "-"
        wdt = self.wdt  # <--- Use the stored watchdog

        uid = self.secrets.get("hackatime_uid", "")
        projects = self.secrets.get("hackatime_projects", [])
        api_key = self.secrets.get("hackatime_api_key", "")

        if api_key:
            import ubinascii
            encoded = ubinascii.b2a_base64(api_key.encode()).decode().strip()
            headers = {"Authorization": "Basic " + encoded, "Accept": "application/json"}
            base_api = "https://hackatime.hackclub.com"

            # --- LAST 7 DAYS ---
            gc.collect()
            if wdt: wdt.feed()
            try:
                r = urequests.get(
                    base_api + "/api/hackatime/v1/users/current/stats/last_7_days",
                    headers=headers, stream=True, timeout=5
                )
                if r.status_code == 200:
                    buf = ""
                    while True:
                        if wdt: wdt.feed() # Pet watchdog during slow loops
                        chunk = r.raw.read(128)
                        if not chunk: break
                        buf += chunk.decode("utf-8", "ignore")
                        idx = buf.find('"human_readable_total":')
                        if idx != -1:
                            start = buf.find('"', idx + 23) + 1
                            if start > 0:
                                end = buf.find('"', start)
                                if end != -1:
                                    self.week = buf[start:end]
                                    break
                        if len(buf) > 256: buf = buf[-128:]
                try: r.raw.close()
                except: pass
                r.close()
                del r
            except Exception as e:
                print("Week stats error:", e)
            gc.collect()

            # --- TODAY ---
            if wdt: wdt.feed()
            try:
                r2 = urequests.get(
                    base_api + "/api/hackatime/v1/users/current/statusbar/today",
                    headers=headers, stream=True, timeout=5
                )
                if r2.status_code == 200:
                    buf = ""
                    while True:
                        if wdt: wdt.feed() # Pet watchdog
                        chunk = r2.raw.read(128)
                        if not chunk: break
                        buf += chunk.decode("utf-8", "ignore")
                        idx = buf.find('"text":')
                        if idx != -1:
                            start = buf.find('"', idx + 7) + 1
                            if start > 0:
                                end = buf.find('"', start)
                                if end != -1:
                                    self.today = buf[start:end]
                                    break
                        if len(buf) > 256: buf = buf[-128:]
                try: r2.raw.close()
                except: pass
                r2.close()
                del r2
            except Exception as e:
                print("Today stats error:", e)
            gc.collect()

                # --- PROJECTS (BADGES) ---
        username = self.secrets.get("hackatime_username", "")
        
        if not uid or not username or not projects:
            return

        base_badge = "https://hackatime.hackclub.com/api/v1/badge/"
        
        for label, slug in projects:
            gc.collect()
            if wdt: wdt.feed()
            try:
                url = base_badge + uid + "/" + username + "/" + slug
                headers_badge = {"User-Agent": "Sprig-Shelby"}
                
                # Fetch the initial URL
                r = urequests.get(url, headers=headers_badge, stream=True, timeout=5)
                
                # If Hackatime tells us to look elsewhere (301, 302, 307, 308)
                if r.status_code in [301, 302, 307, 308]:
                    # Extract the new URL from the Location header
                    # Note: urequests sometimes lowercases headers, sometimes not
                    redirect_url = ""
                    for k, v in r.headers.items():
                        if k.lower() == "location":
                            redirect_url = v
                            break
                            
                    # Close the old connection immediately
                    try: r.raw.close()
                    except: pass
                    r.close()
                    del r
                    gc.collect()
                    
                    if redirect_url:
                        # Follow the redirect!
                        if wdt: wdt.feed()
                        r = urequests.get(redirect_url, headers=headers_badge, stream=True, timeout=5)
                
                # Now process the actual SVG data (either from a 200 or the redirect 200)
                if r.status_code == 200:
                    buf = ""
                    time_str = "0h 0m"
                    while True:
                        if wdt: wdt.feed()
                        chunk = r.raw.read(128)
                        if not chunk: break
                        buf += chunk.decode("utf-8", "ignore")
                        
                        if len(buf) > 512:
                            buf = buf[-256:]
                    
                    last_text_start = buf.rfind("<text")
                    if last_text_start != -1:
                        val_start = buf.find(">", last_text_start) + 1
                        val_end = buf.find("</text>", val_start)
                        if val_end != -1:
                            time_str = buf[val_start:val_end].strip()
                            if time_str.startswith("hackatime:"):
                                time_str = time_str[10:].strip()
                                
                    self.stats.append((label, time_str))
                else:
                    print(f"Badge {slug} HTTP {r.status_code}")
                    self.stats.append((label, "err"))
                    
                try: r.raw.close()
                except: pass
                r.close()
                del r
                
            except Exception as e:
                print("Badge error:", e)
                self.stats.append((label, "-"))
            gc.collect()

    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Hackatime", WHITE, self.font, 1)
        d.text((110, 3), "J:back", GREY, self.font, 1)

        if self.error:
            d.text((8, 40), "Error:", RED, self.font, 1)
            d.text((8, 52), self.error[:15], GREY, self.font, 1)
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
            d.text((8, y), label[:12], WHITE, self.font, 1)
            d.text((100, y), time_str[:10], YELLOW, self.font, 1)
            y += 13

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        if btns["K"].pressed():
            self.show()
        return None