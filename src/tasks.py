import displayio
import terminalio
from adafruit_display_text import label

class TaskScreen(displayio.Group):
    def __init__(self, width, height):
        super().__init__()
        self.tasks = [
            {"text": "Complete 1 chapter in science", "done": False},
            {"text": "Try to log 4 hours for hackatime", "done": False},
            #we can add more like this
        ]
        self.cursor_idx = 0

        bg_bitmap = displayio.Bitmap(width, height, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x111111
        self.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

        self.header = label.Label(terminalio.FONT, text="Todo List (W/S/D/L)", color=0xFFFFFF)
        self.header.anchor_point = (0.5, 0.0)
        self.header.anchored_position = (width // 2, 5)
        self.append(self.header)

        self.list_label = label.Label(terminalio.FONt, text="", color=0x00FF00, line_spacing = 1.2)
        self.list_label.anchor_point = (0.0, 0.0)
        self.list_label.anchored_position = (10, 30)
        self.append(self.list_label)

        self.render_list()

    def render_list(self):
        if not self.tasks:
            self.list_label.text = "All done! Chillax.."
            return
        
        lines = []
        for i, task in enumerate(self.tasks):
            cursor = "> " if i == self.cursor_idx else "  "
            box = "[x]" if task["done"] else "[ ]"
            #Truncating to fix in the screen
            text = task["text"][:16]
            lines.append(f"{cursor}{box} {text}")
        self.list_label.text = "\n".join(lines)
    
    def move_cursor(self, delta):
        if self.tasks:
            self.cursor_idx = (self.cursor_idx + delta) % len(self.tasks)
            self.render_list()

    def toggle_task(self):
        if self.tasks:
            self.tasks[self.cursor_idx]["done"] = not self.tasks[self.cursor_idx]["done"]
            self.render_list()

    def delete_task(self):
        if self.tasks:
            self.tasks.pop(self.cursor_idx)
            if self.cursor_idx >= len(self.tasks) and self.tasks:
                self.cursor_idx = len(self.tasks) - 1
            elif not self.tasks:
                self.cursor_idx = 0
            self.render_list()