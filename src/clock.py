import time
import displayio
import terminalio
from adafruit_display_text import label

class ClockScreen(displaio.Group):
    def __init__(self, display_width=160, display_height=128):
        super().__init__()
        self.width = display_width
        self.height = display_height

        # Background that changes with time [dynamic]

        self.bg_bitmap = displayio.Bitmap(self.width, self.height, 1)
        self.bg_palette = displayio.Palette(1)
        self.bg_palette[0] = 0x000000 #default black bg
        self.bg_sprite = displayio.TileGrid(self.bg_bitmap, pixel_shader=self.bg_palette)
        self.append(self.bg_sprite)

        # Clock label

        self.time_label = label.Label(
            terminalio.FONT,
            text="00:00 AM",
            color=0xFFFFFF,
            scale=3
        )
        self.time_label.anchor_point = (0.5, 0.5)
        self.time_label.anchored_position = (self.width // 2, self.height // 2 - 15)
        self.append(self.time_label)

        # Date label

        self.date_label = label.Label(
            terminalio.FONT,
            text="Jan 01, 2000",
            color=0xDDDDDD,
            scale=1
        )
        self.date_label.anchor_point = (0.5, 0.5)
        self.date_label.anchored_position = (self.width // 2, self.height // 2 + 15)
        self.append(self.date_label)

        # Status/menu label

        self.status_label = label.Label(
            terminalio.FONT,
            text="Loading...",
            color=0xFFFF00,
            scale=1
        )
        self.status_label.anchor_point = (0.5, 1.0)
        self.status_label.anchored_position = (self.width // 2, self.height -5)
        self.append(self.status_label)

        self.last_update_sec = -1

    def update(self):
        now = time.localtime()

        # redraw fixture (Only redraw if the second has changed)
        if now.tm_sec == self.last_update_sec:
            return
        self.last_update_sec = now.tm_sec

        #Apply the dynamic themes
        hour = now.tm_hour
        if 6  <= hour < 12:
            self.bg_palette[0] = 0xFF5500
        elif 12 <= hour < 18:
            self.bg_palette[0] = 0x0088FF
        elif 18 <= hour < 21:
            self.bg_palette[0] = 0x993300
        else:
            self.bg_palette[0] = 0x000022

        # 12-hour format logic
        ampm = "AM"
        hr_12 = hour
        if hour >= 12:
            ampm = "PM"
            if hour > 12:
                hr_12 = hour - 12
        if hr_12 == 0:
            hr_12 = 12

        self.time_label.text = f"{hr_12:02d} : {now.tm_min:02d} {ampm}"

        #Date format logic
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_str = months[now.tm_mon - 1] if 1 <= now.tm_mon <= 12 else "Unknown"
        self.date_label.text = f"{month_str} {now.tm_mday:02d}, {now.tm_year}"
    
    def show_menu_hint(self, index, gh_count=0, mail_count=0):
        """Updates the bottom label based on what is selected in the menu"""
        menus = ["Clock", "GitHub", "Gmail", "Tasks"]
        if index == 0:
            #Home state
            if gh_count > 0: badges.append(f"GH:{gh_count}")
            if mail_count > 0: badges.append(f"Mail:{mail_count}")
            self.status_label.text = " | ".join(badges) if badges else "All caught up!"
            self.status_label.color = 0x00FF00 if not badges else 0xFFFF00
        else:
            self.status_label.text = f"-> Open {menus[index]} (Press D)"
            self.status_label.color = 0xFFFFFF