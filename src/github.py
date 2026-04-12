import st7735
import time
import gc
import urequests
from src.utils import draw_text_on_bg

def _c(r, g, b):
    return ((r & 0xF8) << 8) |((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
TITLE_BG = _c(30, 30, 30)
GREY = _c(120, 120, 120)

#Github shades for contribution graph
C_0 = _c(22, 27, 34) #0 empty (dark grey)
C_1 = _c(14, 68, 41) #Level 1 (lightest green)
C_2 = _c(0, 109, 50) #Level 2
C_3 = _c(38, 166, 65) #Level 3
C_4 = _c(57, 211, 83) #Level 4 (Max green)

class GithubScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.grid = []
        self.error = None
        self.username = self.secrets.get("github_username", "")
        self.token = self.secrets.get("github_token", "")
        self.total_commits = 0

    def _fetch(self):
        gc.collect()
        if not self.username or not self.token:
            self.error = "Missing username/token"
            return
        
        self.error = None
        self.grid = []
        self.total_commits = 0

        #We will use GraphQL API to fetch contribution counts for the last year
        #But it will only show the last 18 weeks to fit the screen
        query = """
        {
            user(login: "%s") {
                contributionsCollection {
                    contributionCalendar {
                        weeks {
                            contributionDays {
                                contributionCount
                            }
                        }
                    }
                }
            }
        }""" % self.username

        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Sprig-Shelby",
            "Content-Type": "application/json"
        }

        #Manually format JSON to save memory
        payload = '{"query": "' + query.replace('\n', ' ').replace('"', '\\"') + '"}'

        try:
            r = urequests.post("https://api.github.com/graphql", headers=headers, data=payload, stream=True, timeout=8)
            if r.status_code == 200:
                buf = ""
                temp_grid = []

                #We are looking for strings like "contributionCount":0
                while True:
                    chunk = r.raw.read(128)
                    if not chunk: break
                    buf += chunk.decode("utf-8", "ignore")

                    while '"contributionCount":' in buf:
                        idx = buf.find('"contributionCount":')
                        end_idx = buf.find('}', idx)

                        if end_idx != -1:
                            val_str = buf[idx+20:end_idx].strip()
                            try:
                                count = int(val_str)
                                temp_grid.append(count)
                            except:
                                pass
                            buf = buf[end_idx:]
                        else:
                            break

                    if len(buf) > 256:
                        buf = buf[-128:]
                        
                #We only want the last 18 weeks (126days) [18col x 7 rows]
                self.grid = temp_grid[-126:] if len(temp_grid) >= 126 else temp_grid
                self.total_commits = sum(self.grid)

            else:
                self.error = f"HTTP {r.status_code}"

            try: r.raw.close()
            except: pass
            r.close()
            del r

        except Exception as e:
            self.error = str(e)[:22]
            print(f"GH Graph error: {e}")

        gc.collect()

    def _get_color(self, count):
        """Map the num of commits to github green shades"""
        if count == 0: return C_0
        if count <= 2: return C_1
        if count <= 5: return C_2
        if count <= 10: return C_3
        return C_4
    
    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        draw_text_on_bg(d, self.font, "Contributions", 8, 3, WHITE, TITLE_BG)
        draw_text_on_bg(d, self.font, "J:back", 115, 3, GREY, TITLE_BG)
        
        if self.error:
            draw_text_on_bg(d, self.font, "Error:" 8, 40, st7735.TFT.RED, BG)
            draw_text_on_bg(d, self.font, self.error, 8, 52, GREY, BG)
            return
        
        if not self.grid:
            draw_text_on_bg(d, self.font, "No data found", 8, 40, GREY, BG)
            return
        
        #Draw the graph
        #the display is 160px wide and graph is 7 days tall and each with 2px gap so we will get total 8px per col/row
        sq_size = 6
        gap = 2
        step = sq_size + gap

        start_x = 8
        start_y = 35

        #Github graph is filled column wise (top to bottom)
        col = 0
        row = 0
        for count in self.grid:
            x = start_x + (col * step)
            y = start_y + (row * step)

            color = self._get_color(count)
            d.fillrect((x, y), (sq_size, sq_size), color)

            row += 1
            if row >= 7:
                row = 0
                col += 1

        #Draw total commits at the bottom
        draw_text_on_bg(d, self.font, f"{self.total_commits} commits (last 18w)", 8, 105, GREY, BG)
        
    def show(self):
        self.display.fill(BG)
        self.display.fillrect((0, 0), (160, 14), TITLE_BG)
        draw_text_on_bg(self.display, self.font, "GitHub", 8, 3, WHITE, TITLE_BG)
        draw_text_on_bg(self.display, self.font, "Loading...", 40, 55, st7735.TFT.GREEN, BG)

        self._fetch()
        self._draw()

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        return None