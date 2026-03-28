import ujson
import time
import st7735
from src.font import FONT

C = st7735.TFT.color

_BG = C(5, 15, 10)
_HEADER = C(20, 80, 50)
_WHITE = C(240, 240, 240)
_DONE = C(60, 90, 65)
_GRAY = C(100, 110, 100)
_GREEN = C(80, 220, 100)
_RED = C(220, 80, 80)
_SEL_BG = C(20, 45, 28)
_ACCENT = C(100, 220, 150)

W = 160
H = 128
CHAR_W = 6
HEADER_H = 14
FOOTER_H = 10
ROW_H = 11
MAX_ROWS = (H - HEADER_H - FOOTER_H) // ROW_H # =9
TASKS_FILE =  "tasks.json"

def _tw(s): return len(s) * CHAR_W
def _cx(s): return (W - _tw(s)) // 2

class TasksScreen:
    def __init__(self, display):
        self.display = display
        self.tasks = []
        self.cursor = 0
        self.scroll = 0
        self._dirty = False
        self._load()

    def draw(self):
        self._fill(0, 0, W, H, _BG)
        self._draw_header()
        self._draw_body()
        self._draw_footer()
    
    def update(self):
        if self._dirty:
            self._save()
            self._dirty = False

    def on_button(self, btn):
        n = len(self.tasks)
        if btn == "W":
            if self.cursor > 0:
                self.cursor -= 1
                if self.cursor < self.scroll:
                    self.scroll = self.cursor
                self._draw_body()
        
        elif btn == "S":
            if self.cursor < n -1:
                self.cursor += 1
                if self.cursor >= self.scroll + MAX_ROWS:
                    self.scroll += 1
                self._draw_body()

        elif btn == "K":
            if self.tasks:
                self.tasks[self.cursor]["done"] = not self.tasks[self.cursor]["done"]
                self._dirty = True
                self._draw_header()
                self._draw_body()

        elif btn == "J":
            if self.tasks:
                self.tasks.pop(self.cursor)
                self.cursor = max(0, min(self.cursor, len(self.tasks) - 1))
                self.scroll = max(0, self.cursor - MAX_ROWS + 1)
                self._dirty = True
                self.draw()

        elif btn == "I":
            #In real use: add new tasks via mpremote import ujson
            #or via serial REPL. This cycles a demo for testing.
            demo = "Task {}".format(len(self.tasks) +  1)
            if len(self.tasks) < 30:
                self.tasks.append({"text": demo, "done": False})
                self._dirty = True
                self.draw()

    #Persistence

    def _load(self):
        try:
            with open(TASKS_FILE, "r") as f:
                data = ujson.load(f)
            if isinstance(data, list):
                self.tasks = data
            else:
                self.tasks = []
        except:
            self.tasks = [
                {"text": "Test the Shelby Firmware", "done": False},
                {"text": "Log 5 hours in hackatime", "done": False},
                #We can add more tasks with this format
            ]
    
    def _save(self):
        try:
            with open(TASKS_FILE, "w") as f:
                ujson.dump(self.tasks, f)
        except Exception as e:
            print("tasks save:", e)

    #Draw screen functions

    def _draw_header(self):
        self._fill(0, 0, W, HEADER_H, _HEADER)
        done = sum(1 for t in self.tasks if t["done"])
        total = len(self.tasks)
        title = "Tasks {}/{}".format(done, total)
        self._text(title, _cx(title), 3, _BG)

    def _draw_body(self):
        y0 = HEADER_H
        bh = H - HEADER_H - FOOTER_H
        self._fill(0, y0, W, bh, _BG)

        if not self.tasks:
            msg = "No tasks. I=add demo"
            self._text(msg, _cx(msg), y0 + bh // 2 - 4, _GRAY)
            return
        
        y = y0 + 1
        visible = self.tasks[self.scroll : self.scroll + MAX_ROWS]
        for i, t in enumerate(visible):
            real_i = i + self.scroll
            is_sel = (real_i == self.cursor)
            self._fill(0, y, W, ROW_H, _SEL_BG if is_sel else _BG)

            check = "[x]" if t["done"] else "[ ]"
            label = check + " " + t["text"][:(W // CHAR_W - 5)]
            color = _DONE if t["done"] else (_GREEN if is_sel else _WHITE)
            self._text(label, 2, y + 1, color)
            y += ROW_H

            #Scrollbar
            if len(self.tasks) > MAX_ROWS:
                sb_h = bh * MAX_ROWS // len(self.tasks)
                sb_y = y0 + bh * self.scroll // len(self.tasks)
                self._fill(W- 2, y0, 2, bh, _HEADER)
                self._fill(W - 2, sb_y, 2, sb_h, _ACCENT)

    def _draw_footer(self):
        self._fill(0, H - FOOTER_H, W, FOOTER_H, _HEADER)
        hint = "W/S:nav K:done J:del"
        self._text(hint, _cx(hint), H - FOOTER_H + 1, _BG)

    def _text(self, s, x, y, color):
        self.display.text((x, y), s, color, FONT, 1)

    def _fill(self, x, y, w, h, color):
        self.display.fillrect((x, y), (w, h), color)