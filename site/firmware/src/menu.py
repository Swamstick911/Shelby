import st7735
from src.icons import draw_github, draw_system, draw_tasks, draw_settings, draw_hackatime, draw_music
from src.utils import draw_text_on_bg

def _c(r, g, b):
    """Convert RGB tuple to 16-bit 565 color integer"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# Colour palette
BG = st7735.TFT.BLACK
TITLE_C = st7735.TFT.WHITE
HINT_C = _c(80, 80, 80)
TITLE_BG = _c(10, 10, 30)

# Card colours
CARD_BG = _c(20, 20, 40)
CARD_SEL = _c(40, 80, 120)
ICON_C = st7735.TFT.WHITE
ICON_SEL_C = st7735.TFT.CYAN
LABEL_C = _c(180, 180, 180)
LABEL_SEL_C = st7735.TFT.WHITE
BORDER_C = _c(60, 60, 100)
BORDER_SEL_C = st7735.TFT.CYAN

# Layout constants
TITLE_H = 14
FOOTER_H = 12
COLS = 3
ROWS = 2
PADDING = 4
GRID_X = PADDING
GRID_Y = TITLE_H + PADDING
GRID_W = 160 - PADDING * 2
GRID_H = 128 - TITLE_H - FOOTER_H - PADDING * 2
CARD_W = (GRID_W - PADDING * (COLS - 1)) // COLS
CARD_H = (GRID_H - PADDING * (ROWS - 1)) // ROWS

APPS = [
    {"id": "github",    "label": "GitHub",    "draw": draw_github},
    {"id": "system",    "label": "System",    "draw": draw_system},
    {"id": "tasks",     "label": "Tasks",     "draw": draw_tasks},
    {"id": "hackatime", "label": "Hakatime", "draw": draw_hackatime},
    {"id": "settings",  "label": "Settings",  "draw": draw_settings},
    {"id": "music",     "label": "Music",     "draw": draw_music},
]
# Navigation: W=up, S=down, A=left, D=right, I=select, J=back

class MenuScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.cursor = 0
        self._drawn = False
        self._prev_cursor = -1

    # Public API

    def show(self):
        """Force a full repaint when entering the menu"""
        self._drawn = False
        self._prev_cursor = -1
        self.draw()

    def draw(self):
        """Smart draw — full repaint first time, only changed cards after"""
        if not self._drawn:
            self._full_draw()
            self._drawn = True
        elif self._prev_cursor != self.cursor:
            self._draw_card(self._prev_cursor)
            self._draw_card(self.cursor)
        self._prev_cursor = self.cursor

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "clock"

        if btns["W"].pressed():
            # Move up one row
            if self.cursor >= COLS:
                self.cursor -= COLS
                self.draw()

        elif btns["S"].pressed():
            # Move down one row
            if self.cursor + COLS < len(APPS):
                self.cursor += COLS
                self.draw()

        elif btns["A"].pressed():
            # Move left
            if self.cursor % COLS != 0:
                self.cursor -= 1
                self.draw()

        elif btns["D"].pressed():
            # Move right
            if self.cursor % COLS != COLS - 1 and self.cursor + 1 < len(APPS):
                self.cursor += 1
                self.draw()

        elif btns["I"].pressed():
            return APPS[self.cursor]["id"]

        return None

    # Private drawing helpers

    def _full_draw(self):
        d = self.display
        d.fill(BG)

        # Title bar
        d.fillrect((0, 0), (160, TITLE_H), TITLE_BG)
        title = "SHELBY OS"
        tx = (160 - len(title) * 6) // 2
        draw_text_on_bg(d, self.font, title, tx, 3, TITLE_C, TITLE_BG)

        # Footer hint
        fy = 128 - FOOTER_H
        d.fillrect((0, fy), (160, FOOTER_H), TITLE_BG)
        hint = "WASD:nav  I:open  J:back"
        hx = (160 - len(hint) * 6) // 2
        draw_text_on_bg(d, self.font, hint, hx, fy + 2, HINT_C, TITLE_BG)

        # Draw all cards
        for i in range(len(APPS)):
            self._draw_card(i)

    def _card_rect(self, index):
        """Returns (x, y, w, h) for card at index in 3x2 grid"""
        row = index // COLS
        col = index % COLS
        x   = GRID_X + col * (CARD_W + PADDING)
        y   = GRID_Y + row * (CARD_H + PADDING)
        return x, y, CARD_W, CARD_H

    def _draw_card(self, index):
        d   = self.display
        app = APPS[index]
        sel = (index == self.cursor)

        x, y, w, h = self._card_rect(index)
        
        # Calculate the background color based on whether it is selected or not
        current_card_bg = CARD_SEL if sel else CARD_BG

        # Card background
        d.fillrect((x, y), (w, h), current_card_bg)

        # Border
        bc = BORDER_SEL_C if sel else BORDER_C
        d.line((x,     y),     (x+w-1, y),     bc)  # top
        d.line((x,     y+h-1), (x+w-1, y+h-1), bc)  # bottom
        d.line((x,     y),     (x,     y+h-1), bc)  # left
        d.line((x+w-1, y),     (x+w-1, y+h-1), bc)  # right

        # Icon
        ic     = ICON_SEL_C if sel else ICON_C
        icon_x = x + (w - 16) // 2
        icon_y = y + 6
        app["draw"](d, icon_x, icon_y, ic)

        # Label
        label = app["label"]
        lw    = len(label) * 6
        lx    = x + (w - lw) // 2
        ly    = y + h - 10
        lc    = LABEL_SEL_C if sel else LABEL_C
        
        draw_text_on_bg(d, self.font, label, lx, ly, lc, current_card_bg)