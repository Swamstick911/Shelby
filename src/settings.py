import st7735
import gc
import machine
import network

def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED
CYAN = st7735.TFT.CYAN
YELLOW = _c(255, 220, 0)
GREY = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)
SEL_BG = _c(20, 40, 60)

ITEMS = [
    "12/24h clock",
    "re-sync NTP",
    "System info",
    "Board",
    "IP address",
    "Free RAM",    
]
INTERACTIVE = {0, 1}

class SettingsScreen:
    def __init__(self, display, font, secrets, wifi_mgr=None):
        self.display = display
        self.font = font
        self.secrets = secrets
        self.wifi_mgr = wifi_mgr
        self.cursor = 0
        self.use_24h = False
        self._status = ""
        self._status_color = GREEN

    def show(self):
        self.cursor = 0
        self._status = ""
        self._draw()

    def _get_ip(self):
        try:
            wlan = network.WLAN(network.STA_IF)
            return wlan.ifconfig()[0]
        except:
            return "No WiFi"
    
    def _get_ram(self):
        gc.collect()
        free = gc.mem_free()
        if free >= 1024:
            return str(free // 1024) + " KB free"
        return str(free) + " B free"

    def _get_board(self):
        try:
            return machine.unique_id().hex()[:12]
        except:
            return "Pico W"
        
    def _row_value(self, index):
        """Returns the right-hand value string for each row"""
        if index == 0:
            return "24h" if self.use_24h else "12h"
        if index == 1:
            return "D to sync"
        if index == 2:
            return ""
        if index == 3:
            return self._get_board()
        if index == 4:
            return self._get_ip()
        if index == 5:
            return self._get_ram()
        return ""
    
    def _draw(self):
        d = self.display
        d.fill(BG)

        #Title bar
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Settings", WHITE, self.font, 1)
        d.text((110, 3), "A:back", GREY, self.font, 1)

        #footer
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((0, 118), "W/S:nav   D:select", GREY, self.font, 1)

        #status message line
        if self._status:
            sx = (160 - len(self._status) * 6) // 2
            d.text((sx, 106), self._status, self._status_color, self.font, 1)

        #Draw rows
        y = 18
        for i, label in enumerate(ITEMS):
            sel = (i == self.cursor)
            is_header = (i == 2)

            if is_header:
                lx = (160 - len(label) * 6) // 2
                d.text((lx, y), label, GREY, self.font, 1)
                y += 15
                continue

            #Arrow on selected interactive row
            if sel and i in INTERACTIVE:
                d.text((2, y), ">", CYAN, self.font, 1)

            #label
            lc = CYAN if (sel and i in INTERACTIVE) else WHITE
            d.text((12, y), label, lc, self.font, 1)

            #value
            val = self._row_value(i)
            if val:
                vx = 158 - len(val) * 6
                vc = YELLOW if (sel and i in INTERACTIVE) else GREY
                d.text((vx, y), val, vc, self.font, 1)

            y += 15

    def _draw_row(self, index):
        """Redraw a single row without full repaint"""
        y = 18
        for i in range(index + 1):
            if i == 2:
                y += 15
                continue
            if i == index:
                break
            y += 15

        d = self.display
        sel = (index == self.cursor)
        is_header = (index == 2)

        #clear the row
        d.fillrect((0, y - 1), (160, 13), BG)

        if is_header:
            label = ITEMS[index]
            lx = (160 - len(label) * 6) // 2
            d.text((lx, y), label, GREY, self.font, 1)
            return
        
        if sel:
            d.fillrect((0, y - 1), (160, 13), SEL_BG)

        if sel and index in INTERACTIVE:
            d.text((2, y), ">", CYAN, self.font, 1)

        lc = CYAN if (sel and index in INTERACTIVE) else WHITE
        d.text((12, y), ITEMS[index], lc, self.font, 1)

        val = self._row_value(index)
        if val:
            vx = 158 - len(val) * 6
            vc = YELLOW if (sel and index in INTERACTIVE) else GREY
            d.text((vx, y), val, vc, self.font, 1)

    def handle_input(self, btns):
        if btns["A"].pressed():
            return "menu"
        
        if btns["W"].pressed():
            prev = self.cursor
            self.cursor = (self.cursor - 1) % len(ITEMS)
            #Skip section header
            if self.cursor == 2:
                self.cursor = 1
            self._draw_row(prev)
            self._draw_row(self.cursor)

        elif btns["S"].pressed():
            prev = self.cursor
            self.cursor = (self.cursor + 1) % len(ITEMS)
            #Skip section header
            if self.cursor == 2:
                self.cursor = 3
            self._draw_row(prev)
            self._draw_row(self.cursor)

        elif btns["D"].pressed():
            if self.cursor == 0:
                #Toggle 12/24h
                self.use_24h = not self.use_24h
                self._status = "24h on!" if self.use_24h else "12h on!"
                self._status_color = GREEN
                self._draw()

            elif self.cursor == 1:
                #Re-sync NTP
                if self.wifi_mgr:
                    self._status = "Syncing..."
                    self._status_color = YELLOW
                    self._draw()
                    try:
                        self.wifi_mgr.sync_time()
                        self._status = "Time Synced!"
                        self._status_color = GREEN
                    except Exception as e:
                        self._status = "Sync failed"
                        self._status_color = RED
                    self._draw()
                else:
                    self._status = "No WiFi mgr"
                    self._status_color = RED
                    self._draw()

            return None