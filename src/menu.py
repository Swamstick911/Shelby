import st7735
from src.icons import draw_github, draw_gmail, draw_tasks, draw_settings, draw_hackatime

def _c(r, g, b):
    """Convert RGB tuple to 16-bit 565 color integer"""
    return((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

#colour palette
BG = st7735.TFT.BLACK
TITLE_C = st7735.TFT.WHITE
HINT_C = _c(80, 80, 80)

#Card colours
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
GRID_Y = TITLE_H + 2
GRID_H = 128 - TITLE_H - FOOTER_H - 4
CARD_W = 72
CARD_H = (GRID_H // 3) - 2
COL0_X = 8
COL1_X = COL0_X + CARD_W + 8
ROW0_Y = GRID_Y
ROW1_Y = GRID_Y + CARD_H + 3
ROW2_Y = GRID_Y + (CARD_H + 3) * 2

APPS = [
    {"id": "github", "label": "GitHub", "draw": draw_github},
    {"id": "gmail", "label": "Gmail", "draw": draw_gmail},
    {"id": "tasks", "label": "Tasks", "draw": draw_tasks},
    {"id": "settings", "label": "Settings", "draw": draw_settings},
    {"id": "hackatime", "label": "Hackatime", "draw": draw_hackatime},
    {"id": "none", "label": "More soon", "draw": draw_settings}, #placeholder

]
# Flat order for cursor: 0= Github, 1= Gmail, 2= Tasks, 3= Settings
# W=prev, S=next {wraps}, D= Select, A= Back

class MenuScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.cursor = 0
        self._drawn = False
        self._prev_cursor = -1

    # Public API

    def show(self):
        """Force a full repaint call when entering the menu"""
        self._drawn = False
        self._prev_cursor = -1
        self.draw()

    def draw(self):
        """Smart draw, full repaint on the first show card only on cusror move"""
        if not self._drawn:
            self._full_draw()
            self._drawn = True
        elif self._prev_cursor != self.cursor:
            #Only redraw when the two cards that changed
            self._draw_card(self._prev_cursor)
            self._draw_card(self.cursor)
        self._prev_cursor = self.cursor

    def handle_input(self, btns):
        """
        Call every loop tick
        returns:
        "clock" - A pressed go back to clock screen
        app id str - D pressed to open the app
        none - no navigation event
        """

        if btns["A"].pressed():
            return "clock"

        elif btns["W"].pressed():
            self.cursor = (self.cursor - 1) % len(APPS)
            self.draw()

        elif btns["S"].pressed():
            self.cursor = (self.cursor + 1) % len(APPS)
            self.draw()

        elif btns["D"].pressed():
            return APPS[self.cursor]["id"]
        
        return None
    
    # Private drawing helpers

    def _full_draw(self):
        d = self.display
        d.fill(BG)

        # Title bar
        d.fillrect((0, 0), (160, TITLE_H), _c(10, 10, 30))
        title = "SHELBY OS"
        tx = (160 - len(title) * 6) // 2
        d.text((tx, 3), title, TITLE_C, self.font, 1)

        # Footer hint
        fy = 128 - FOOTER_H
        d.fillrect((0, fy), (160, FOOTER_H), _c(10, 10, 30))
        hint = "W/S:nav D:open A:back"
        hx = (160 - len(hint) * 6) // 2
        d.text((hx, fy + 2), hint, HINT_C, self.font, 1)

        # Draw all 4 cards
        for i in range(len(APPS)):
            self._draw_card(i)

    def _card_rect(self, index):
        """Returns (x, y, w, h) for the card"""
        row = index // 2
        col = index % 2
        x = COL0_X if col == 0 else COL1_X
        if row == 0:
            y = ROW0_Y
        elif row == 1:
            y = ROW1_Y
        else:
            y = ROW2_Y
        return x, y, CARD_W, CARD_H

    def _draw_card(self, index):
        d   = self.display
        app = APPS[index]
        sel = (index == self.cursor)

        x, y, w, h = self._card_rect(index)

        # Card background
        bg_col = CARD_SEL if sel else CARD_BG
        d.fillrect((x, y), (w, h), bg_col)

        # Border — drawn as 4 lines (driver has no rect outline method)
        bc = BORDER_SEL_C if sel else BORDER_C
        d.line((x,     y),     (x+w-1, y),     bc)  # top
        d.line((x,     y+h-1), (x+w-1, y+h-1), bc)  # bottom
        d.line((x,     y),     (x,     y+h-1), bc)  # left
        d.line((x+w-1, y),     (x+w-1, y+h-1), bc)  # right

        # Arrow indicator when selected
        if sel:
            d.text((x + 2, y + 2), ">", ICON_SEL_C, self.font, 1)

        # Icon — centred in the upper portion of the card
        icon_x = x + (w - 16) // 2
        icon_y = y + 4
        ic = ICON_SEL_C if sel else ICON_C
        app["draw"](d, icon_x, icon_y, ic)

        # Label — centred at the bottom of the card
        label = app["label"]
        lw    = len(label) * 6
        lx    = x + (w - lw) // 2
        ly    = y + h - 10
        lc    = LABEL_SEL_C if sel else LABEL_C
        d.text((lx, ly), label, lc, self.font, 1)