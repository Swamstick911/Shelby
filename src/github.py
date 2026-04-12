import st7735
import time
import gc
import urequests
from src.utils import draw_text_on_bg

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
TITLE_BG = _c(30, 30, 30)
GREY = _c(120, 120, 120)

# GitHub's exact 5 shades of green for the contribution graph
C_0 = _c(22, 27, 34)       # Level 0 (Empty / Dark Grey)
C_1 = _c(14, 68, 41)       # Level 1 (Lightest Green)
C_2 = _c(0, 109, 50)       # Level 2 
C_3 = _c(38, 166, 65)      # Level 3
C_4 = _c(57, 211, 83)      # Level 4 (Max Green)

class GithubScreen:
    def __init__(self, display, font, secrets, wdt=None):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.wdt = wdt
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

        # GraphQL Query for the last year of contributions
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
        }
        """ % self.username

        headers = {
            "Authorization": "bearer {}".format(self.token),
            "User-Agent": "Sprig-Shelby",
            "Content-Type": "application/json"
        }
        
        payload = '{"query": "' + query.replace('\n', ' ').replace('"', '\\"') + '"}'
        
        try:
            if self.wdt: self.wdt.feed()
            # Force garbage collection right before the massive RAM spike of the TLS Handshake
            gc.collect() 
            
            # The timeout here is 15 seconds to give the SSL handshake plenty of time
            r = urequests.post("https://api.github.com/graphql", headers=headers, data=payload, stream=True, timeout=15)
            
            if r.status_code == 200:
                buf = ""
                temp_grid = []
                
                while True:
                    if self.wdt: self.wdt.feed()
                    chunk = r.raw.read(128)
                    if not chunk: break
                    buf += chunk.decode("utf-8", "ignore")
                    
                    while '"contributionCount":' in buf:
                        if self.wdt: self.wdt.feed()
                        idx = buf.find('"contributionCount":')
                        end_idx = buf.find('}', idx)
                        
                        if end_idx != -1:
                            val_str = buf[idx+20:end_idx].strip()
                            try:
                                temp_grid.append(int(val_str))
                            except:
                                pass
                            buf = buf[end_idx:]
                        else:
                            break
                            
                    if len(buf) > 256:
                        buf = buf[-128:]
                        
                # Only keep last 126 days (18 weeks x 7 days)
                self.grid = temp_grid[-126:] if len(temp_grid) >= 126 else temp_grid
                self.total_commits = sum(self.grid)
                
            else:
                self.error = "HTTP {}".format(r.status_code)
                
            try: r.raw.close()
            except: pass
            r.close()
            del r
            
        except Exception as e:
            self.error = str(e)[:22]
            print("GH Graph error: {}".format(e))
            
        gc.collect()

    def _get_color(self, count):
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
            # Fixed the missing comma on this line!
            draw_text_on_bg(d, self.font, "Error:", 8, 40, st7735.TFT.RED, BG)
            draw_text_on_bg(d, self.font, self.error, 8, 52, GREY, BG)
            return

        if not self.grid:
            draw_text_on_bg(d, self.font, "No data found.", 8, 40, GREY, BG)
            return
        
        sq_size = 6
        gap = 2
        step = sq_size + gap
        
        start_x = 8
        start_y = 35
        
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

        commit_str = "{} commits (18w)".format(self.total_commits)
        draw_text_on_bg(d, self.font, commit_str, 8, 105, GREY, BG)

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