import st7735
import time
import gc
from src.utils import draw_text_on_bg

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
TITLE_BG = _c(60, 0, 120)  # Purple theme for games
GREY = _c(150, 150, 150)
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED

class GamesScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.games = []
        self.error = None
        self.last_fetch = 0

    def _fetch(self):
        import gc
        gc.collect()
        try:
            import urequests
            headers = {"User-Agent": "Sprig-Shelby"}
            r = urequests.get(
                "https://api.github.com/repos/hackclub/sprig/contents/games",
                headers=headers,
                stream=True
            )
            
            if r.status_code == 200:
                self.games = []
                buf = ""
                # Read larger chunks to make sure we don't slice a name in half
                while len(self.games) < 5:
                    chunk = r.raw.read(256)
                    if not chunk:
                        break
                    
                    buf += chunk.decode("utf-8", "ignore")
                    
                    # Keep processing as long as we find '"name":"'
                    while '"name":"' in buf and len(self.games) < 5:
                        start_idx = buf.find('"name":"') + 8
                        end_idx = buf.find('"', start_idx)
                        
                        # If we haven't received the full name yet, wait for next chunk
                        if end_idx == -1:
                            break
                            
                        filename = buf[start_idx:end_idx]
                        
                        if filename.endswith(".js"):
                            name = filename[:-3] # Remove .js
                            if len(name) > 22:
                                name = name[:21] + "~"
                            self.games.append(name)
                            
                        # Move the buffer forward past this name
                        buf = buf[end_idx:]
                        
                    # Keep buffer small so we don't run out of RAM
                    if len(buf) > 512:
                        buf = buf[-256:]
                        
                self.error = None
            else:
                self.error = "HTTP " + str(r.status_code)
            r.close()
            del r
        except Exception as e:
            self.error = str(e)[:22]
            print(f"Games fetch error: {e}")
        gc.collect()
        self.last_fetch = time.ticks_ms()

    def _draw(self):
        d = self.display
        f = self.font
        
        # Draw the title bar
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        draw_text_on_bg(d, f, "Spade Games", 8, 3, WHITE, TITLE_BG)
        draw_text_on_bg(d, f, "J:back", 115, 3, GREY, TITLE_BG)

        # Draw content
        y = 24
        if self.error:
            draw_text_on_bg(d, f, "Error:", 8, y, RED, BG)
            draw_text_on_bg(d, f, self.error, 8, y+15, WHITE, BG)
        elif not self.games:
            draw_text_on_bg(d, f, "Loading games...", 8, y, GREEN, BG)
        else:
            for g in self.games:
                draw_text_on_bg(d, f, ">", 8, y, GREEN, BG)
                draw_text_on_bg(d, f, g, 20, y, WHITE, BG)
                y += 18

    def show(self):
        self.display.fill(BG)
        self._draw()
        
        if not self.games or time.ticks_diff(time.ticks_ms(), self.last_fetch) > 3600000:
            self._fetch()
            self.display.fill(BG)
            self._draw()

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        return None