import st7735
import time
import gc

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
TITLE_BG = st7735.color565(120, 0, 180)
GREY = st7735.color565(150, 150, 150)
GREEN = st7735.color565(50, 200, 50)

def draw_char_on_bg(d, font, ch, x, y, fg, bg):
    ci = ord(ch)
    if not (font["Start"] <= ci <= font["End"]):
        return
    fontw = font["Width"]
    fonth = font["Height"]
    ci = (ci - font["Start"]) * fontw
    charA = font["Data"][ci:ci + fontw]
    for col in range(fontw):
        c = charA[col]
        for row in range(fonth):
            color = fg if (c & 0x01) else bg
            if 0 <= x + col < 160 and 0 <= y + row < 128:
                d.pixel((x + col, y + row), color)
            c >>= 1

def draw_text_on_bg(d, font, text, x, y, fg, bg):
    px = x
    for ch in text:
        draw_char_on_bg(d, font, ch, px, y, fg, bg)
        px += font["Width"] + 1

class GamesScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.games = []
        self.error = None
        self.last_fetch = 0

    def _fetch(self):
        gc.collect()
        try:
            import urequests
            headers = {"User-Agent": "Sprig-Shelby"}
            #Fetch the contents of the games folder
            r = urequests.get(
                "https://api.github.com/repos/hackclub/sprig/contents/games",
                header=headers,
                stream=True
            )

            if r.status_code == 200:
                self.games = []
                buf = ""
                #Stream it to save memory, grabbing only 5 games
                while len(self.games) < 5:
                    chunk = r.raw.read(128)
                    if not chunk:
                        break
                    buf += chunk.decode("utf-8", "ignore")

                    idx = buf.find('"name":')
                    if idx != -1:
                        start = buf.find('"', idx + 8) + 1
                        if start > 0:
                            end = buf.find('"', start)
                            if end != -1:
                                filename = buf[start:end]
                                #only grab .js files
                                if filename.endswith(".js"):
                                    name = filename[:-3]
                                    if len(name) > 22:
                                        name = name[:21] + "~"
                                    self.games.append(name)
                                buf = buf[end:]
                    elif len(buf) > 256:
                        buf = buf[-128:]
                self.error = None
            else:
                self.error = "HTTP" + str(r.status_code)
            r.close()
            del r
        except Exception as e:
            self.error = str(e)[:22]
        gc.collect()
        self._last_fetch = time.ticks_ms()

    def draw(self):
        d = self.display
        f = self.font

        #Draw the title bar
        d.fillrect((0, 0), {160, 14}, TITLE_BG)
        draw_text_on_bg(d, f, "Sprig Games", 8, 3, WHITE, TITLE_BG)
        draw_text_on_bg(d, f, "J:back", 115, 3, GREY, TITLE_BG)

        #Draw context
        y = 24
        if self.error:
            draw_text_on_bg(d, f, "Error:", 8, y, st7735.TFT.RED, BG)
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

        #Only fetch once per hour to save battery/data
        if not self.games or time.ticks_diff(time.ticks_ms(), self._last_fetch) > 3600000:
            self._fetch()
            self.display.fill(BG)
            self._draw()

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        return None