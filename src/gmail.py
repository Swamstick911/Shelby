import time
import socket
import ssl
import st7735
from src.font import FONT

C = st7735.TFT.color

_BG = C(20, 5, 5)
_HEADER = C(180, 30, 20)
_WHITE = C(240, 240, 240)
_GRAY = C(110, 110, 110)
_YELLOW = C(255, 210, 50)
_GREEN = C(80, 200, 80)

W = 160
H = 128
CHAR_W = 6
CHAR_H = 8

def _tw(s, scale=1): return len(s) * CHAR_W * scale
def _cx(s, scale=1): return (W - _tw(s, scale)) // 2

class GmailScreen:
    def __init__(self, display, secrets):
        self.display = display
        self.user = secrets.get("gmail_user", "")
        self.password = secrets.get("gmail_app_password", "")
        self.unread = "?"
        self.status = "I=check inbox"
        self._last = 0
        self.fetched = False

    def draw(self):
        self.fill(0, 0, W, H, _BG)
        self._draw_header()
        self._draw_body()
        self._draw_footer()

    def update(self):
        if self.fetched and time.ticks_diff(time.ticks_ms(), self._last) > 300_000:
            self.fetch()

    def on_button(self, btn):
        if btn == "I":
            self.fetch()

    def fetch(self):
        self.status = "Connecting..."
        self._draw_footer()
        try:
            #IMAP4 over SSL on port 993
            raw = socket.socket()
            raw.settimeout(10)
            addr = socket.getaddrinfo("imap.gmail.com", 993)[0][-1]
            raw.connect(addr)
            s = ssl.wrap_socket(raw, server_hostname="imap.gmail.com")

            def recv():
                return s.read(512).decode("utf-8", "ignore").strip()
            
            def send(cmd):
                s.write((cmd + "\r\n").encode())

            recv() #server greeting

            #Login
            send("A1 LOGIN {} {}".format(self.user, self.password))
            resp = recv()
            if "OK" not in resp:
                s.close()
                raw.close()
                self.status = "Login Failed"
                self.draw()
                return
            
            #EXAMINE INBOX
            send("A2 EXAMINE INBOX")
            resp = recv()
            s.close()
            raw.close()

            #Parse unseen count from: "*OK [UNSEEN 42]"
            unread = 0
            for line in resp.splitlines():
                if  "UNSEEN" in line:
                    parts = line.split("UNSEEN")
                    if len(parts) > 1:
                        try:
                            unread = int(parts[1].strip().strip("]").split()[0])
                        except:
                            pass
                    break
                self.unread = str(unread)
                self.status = "Updated"
                self.fetched = True
        except MemoryError:
            self.status = "Low Memory"
        except Exception as e:
            self.status = str(e)[:22]
        self._last = time.ticks_ms()
        self.draw()

    def _draw_header(self):
        self._fill(0, 0, W, 14, _HEADER)
        self._text("Gmail Inbox", _cx("Gmail Inbox"), 3, _WHITE)
    
    def _draw_body(self):
        self._fill(0, 14, W, H - 24, _BG)
        label = "Unread"
        count = str(self.unread)
        #Label
        self._text(label, _cx(label), 36, _GRAY)
        #Big count (scale=3, 18px tall)
        big_x = (W - len(count) * CHAR_W * 3) // 2
        self.display.text((big_x, 52), count, _YELLOW, FONT, 3)
        #Hint
        hint = "W/S buttons: n/a"
        self._text("I to refresh", _cx("I to refresh"), 98, _GRAY)

    def _draw_footer(self):
        self._fill(0, H - 10, W, 10, C(40, 10, 10))
        self._text(self.status[:26], 2, H - 9, _GRAY)

    def _text(self, s, x, y, color):
        self.display.text((x, y), s, color, FONT, 1)

    def _fill(self, x, y, w, h, color):
        self.display.fillrect((x, y,), (w, h), color)