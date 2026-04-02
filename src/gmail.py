import st7735
import gc

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) |(b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED
CYAN = st7735.TFT.CYAN
GREY = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)

class GmailScreen:
    def __init__(self, display, font, secrets):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.count = 0
        self.error = None

    def show(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Gmail", WHITE, self.font, 1)
        d.text((110, 3), "A:back", GREY, self.font, 1)
        d.text((50, 55), "Connecting...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _fetch(self):
        gc.collect()
        try:
            import ussl, socket
            user = self.secrets.get("gmail_user", "")
            password = self.secrets.get("gmail_app_password", "")

            addr = socket.getaddrinfo("imap.gmail.com", 993)[0][-1]
            s = socket.socket()
            s.connect(addr)
            s = ussl.wrap_socket(s, server_hostname="imap.gmail.com")

            def recv():
                return s.read(512).decode()
            
            recv()
            s.write(b"A1 LOGIN " + user.encode() + b" " + password.encode() + b"\r\n")
            recv()
            s.write(b"A2 STATUS INBOX (UNSEEN)\r\n")
            resp = recv()
            s.write(b"A3 LOGOUT\r\n")
            s.close()

            #Parse UNSEEN count from response
            import ure
            m = ure.search(r"UNSEEN (\d+)", resp)
            self.count = int(m.group(1)) if m else 0
            self.error = None
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
        
        if self.count == 0:
            d.text((20, 50), "Inbox is empty!", GREEN, self.font, 1)
            d.text((30, 64), "All caught up!", GREEN, self.font, 1)
        else:
            count_str = str(self.count)
            cx = (160 - len(count_str) * 18) // 2
            d.text((cx, 30), count_str, CYAN, self.font, 3)
            label = "unread email" + ("s" if self.count != 1 else "")
            lx = (160 - len(label) * 6) // 2
            d.text((lx, 72), label, WHITE, self.font, 1)

    def handle_input(self, btns):
        if btns["A"].pressed():
            return "menu"
        return None