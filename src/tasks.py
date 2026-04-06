import st7735
import ujson
import gc

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED
CYAN = st7735.TFT.CYAN
GREY = _c(120, 120, 120)
YELLOW = _c(255, 220, 0)
TITLE_BG = _c(10, 10, 30)
TASKS_FILE = "tasks.json"

class TaskScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.tasks = []
        self.cursor = 0
        self.mode = "view"
        self._load()

    def show(self):
        self.mode = "view"
        self._draw()
        
    def _load(self):
        try:
            with open(TASKS_FILE, "r") as f:
                self.tasks = ujson.load(f)
        except:
            self.tasks = []

    def _save(self):
        try:
            with open(TASKS_FILE, "w") as f:
                ujson.dump(self.tasks, f)
        except:
            pass

    def _draw(self):
        d = self.display
        d.fill(BG)

        #title bar
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Tasks", WHITE, self.font, 1)
        count_str = str(len([t for t in self.tasks if not t["done"]])) + " left"
        d.text((110, 3), count_str, CYAN, self.font, 1)

        #Footer
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((4, 118), "I:done L:del K:sync", GREY, self.font, 1)

        if not self.tasks:
            d.text((20, 55), "No tasks!", GREY, self.font, 1)
            d.text((14, 68), "Add via tasks.json", GREY, self.font, 1)
            return
        
        #Task list (shows upto 7 items)
        visible = 7
        start = max(0, self.cursor - visible + 1)
        y = 18
        for i in range(start, min(start + visible, len(self.tasks))):
            task = self.tasks[i]
            sel = (i == self.cursor)

            #Cursor highlight
            if sel:
                d.fillrect((0, y - 1), (160, 13), _c(20, 40 , 60))

            #Checkbox
            if task["done"]:
                d.text((4, y), "[x]", GREEN, self.font, 1)
            else:
                d.text((4, y), "[ ]", GREY, self.font, 1)


            #Task text
            text = task["text"]
            if len(text) > 18:
                text = text[:17] + "~"
            color = GREY if task["done"] else (WHITE if not sel else CYAN)
            d.text((28, y), text, color, self.font, 1)

            y += 14
    
    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"
        
        if not self.tasks:
            if btns["K"].pressed():
                self._load()
                self._draw()
            return None
        
        if btns["W"].pressed():
            self.cursor = max(0, self.cursor - 1)
            self._draw()

        elif btns["S"].pressed():
            self.cursor = min(len(self.tasks) - 1, self.cursor + 1)
            self._draw()

        elif btns["I"].pressed():
            #Toggle done
            self.tasks[self.cursor]["done"] = not self.tasks[self.cursor]["done"]
            self._save()
            self._draw()

        elif btns["L"].pressed():
            #Delete task
            del self.tasks[self.cursor]
            if self.cursor >= len(self.tasks) and self.cursor > 0:
                self.cursor -= 1
            self._save()
            self._draw()
        
        elif btns["K"].pressed():
            self._load()
            self.cursor = 0
            self._draw()

        return None