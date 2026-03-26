import displayio
import terminalio
from adafruit_display_text import label

class GmailScreen(displayio.Group):
    def __init__(self, width, height, requests_session, token):
        super().__init__()
        self.requests = requests_session
        self.token = token
        self.unread_count = 0

        bg_bitmap = displayio.Bitmap(width, height, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x880000 #dark red
        self.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

        self.header = label.Label(terminalio.FONT, text="Unread Emails", color=0xFFFFFF)
        self.header.anchor_point = (0.5, 0.0)
        self.header.anchored_position = (width // 2, 5)
        self.append(self.header)

        self.list_label = label.Label(terminalio.FONT, text="Loading...", color=0xDDDDDD, line_spacing=0.8)
        self.list_label.anchor_point = (0.0, 0.0)
        self.list_label.anchored_position = (5, 25)
        self.append(self.list_label)

    def fetch(self):
        if not self.requests or not self.token:
            self.list_label.text = "Offline or missing token"
            return
        
        headers = {
            "Authorisation": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            print("Fetching Gmail...")
            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages>q=is:unread&maxResults=3"
            resp = self.requests.get(url, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                messages = data.get("messages", [])

                #Estimate total count
                self.unread_count = data.ge("resultSizeEstimate", 0)

                if not messages:
                    self.list_label.text = "Inbox Zero!!"
                else:
                    lines=[]
                    #We have IDs, but need to fetch details for subjects.
                    # To save RAM and API calls, just showing ID snippet or generic msg

                    for msg in messages:
                        lines.append(f"Msg ID: {msg['id'][:8]}...")

                    self.list_label.text = f"Total Unread:{self.unread_count}\n\n" + "\n".join(lines)
            else:
                self.list_label.text = f"Auth Error {resp.status_code}"
            resp.close()
        except Exception as e:
            self.list_label.text = "Fetch failed."
            print(f"Gmail Error: {e}")