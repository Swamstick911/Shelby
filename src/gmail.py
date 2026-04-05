import st7735
import gc
import urequests

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

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
        d.text((110, 3), "A:back", GREY,  self.font, 1)
        d.text((45, 55), "Fetching...", GREEN, self.font, 1)
        self._fetch()
        self._draw()

    def _refresh_token(self):
        """Get a fresh access token using the refresh token."""
        gc.collect()
        data = (
            "client_id="     + self.secrets.get("gmail_client_id", "") +
            "&client_secret="+ self.secrets.get("gmail_client_secret", "") +
            "&refresh_token="+ self.secrets.get("gmail_refresh_token", "") +
            "&grant_type=refresh_token"
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = urequests.post(
            "https://oauth2.googleapis.com/token",
            data=data,
            headers=headers
        )
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            r.close()
            gc.collect()
            return token
        r.close()
        gc.collect()
        return None

    def _fetch(self):
        gc.collect()
        try:
            #Get fresh access token
            token = self._refresh_token()
            if not token:
                self.error = "Token refresh fail"
                return

            headers = {"Authorization": "Bearer " + token}

            #Fetch unread count from inbox
            r = urequests.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                "?labelIds=INBOX&labelIds=UNREAD&maxResults=1",
                headers=headers
            )
            if r.status_code == 200:
                data = r.json()
                self.count = data.get("resultSizeEstimate", 0)
                self.error = None
            else:
                self.error = "HTTP " + str(r.status_code)
            r.close()

        except Exception as e:
            self.error = str(e)[:22]
            print("Gmail error:", e)
        gc.collect()

    def _draw(self):
        d = self.display
        d.fillrect((0, 16), (160, 100), BG)

        if self.error:
            d.text((8, 50), "Error:", RED, self.font, 1)
            d.text((8, 62), self.error, RED, self.font, 1)
            return

        if self.count == 0:
            d.text((20, 50), "Inbox is empty!", GREEN, self.font, 1)
            d.text((30, 64), "All caught up!",  GREEN, self.font, 1)
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