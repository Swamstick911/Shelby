import displayio
import terminalio
from adafruit_display_text import label

class GitHubScreen(displayio.Group):
    def __init__(self, width, height, requests_session, token):
        super().__init__()
        self.requests = requests_session
        self.token = token
        self.unread_count = 0

        #Background
        bg_bitmap = displayio.Bitmap(width, height, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x24292E #github dark theme color
        self.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

        #Header
        self.header = label.Label(terminalio.FONT, text="Github Notifications", color=0xFFFFFF)
        self.header.anchor_point = (0.5, 0.0)
        self.header.anchored_position = (width // 2, 5)
        self.append(self.header)

        #List of items
        self.list_label = label.Label(terminalio.FONT, text="Loading...", color=0xCCCCCC, line_spacing=0.8)
        self.list_label,anchor_point = (0.0, 0.0)
        self.list_label.anchored_position = (5, 25)
        self.append(self.list_label)

    def fetch(self):
        if not self.requests or not self.token:
            self.list_label.text = "Offline or missing token"
            return
        
        headers = {
            "Authorisation": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sprig-Shelby"
        }

        try:
            print("Fetching GitHub")
            resp = self.requests.get("https://api.github.com/notifications",headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                self.unread_count = len(data)
                
                if self.unread_count == 0:
                    self.list_label.text = "Inbox Zero!!"
                else:
                    lines = []
                    #grab only the top 4 so we don't overflow the screen
                    for item in data[:4]:
                        title = item['subject']['title'][:22] # truncate long lines
                        lines.append(f"- {title}")
                    self.list_label.text = "\n\n".join(lines)
            else:
                self.list_label.text = f"API Error: {resp.status_code}"
            resp.close()
        except Exception as e:
            self.list_label.text = "Fetch failed"
            print(f"GH Error: {e}")