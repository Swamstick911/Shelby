import st7735
import gc
import machine
import network


def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BG       = st7735.TFT.BLACK
WHITE    = st7735.TFT.WHITE
GREEN    = st7735.TFT.GREEN
RED      = st7735.TFT.RED
CYAN     = st7735.TFT.CYAN
YELLOW   = _c(255, 220, 0)
GREY     = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)
SEL_BG   = _c(20, 40, 60)

CPU_MODES = [
    ("Normal",    125_000_000),
    ("Turbo",     200_000_000),
    ("Overclock", 250_000_000),
]

PAGE0 = [
    "12/24h clock",
    "CPU mode",
    "Volume",
    "Re-sync NTP",
]

PAGE1 = [
    "Board ID",
    "IP address",
    "Free RAM",
    "CPU speed",
]


class SettingsScreen:
    def __init__(self, display, font, secrets, wifi_mgr=None):
        self.display       = display
        self.font          = font
        self.secrets       = secrets
        self.wifi_mgr      = wifi_mgr
        self.cursor        = 0
        self.page          = 0
        self.use_24h       = False
        self.cpu_mode      = 0
        self.volume        = 50
        self._vol_hold     = 0
        self._status       = ""
        self._status_color = GREEN

    def show(self):
        self.cursor    = 0
        self.page      = 0
        self._status   = ""
        self._vol_hold = 0
        self._draw()

    # ── value helpers ─────────────────────────────────────────────────────────

    def _get_ip(self):
        try:
            return network.WLAN(network.STA_IF).ifconfig()[0]
        except:
            return "No WiFi"

    def _get_ram(self):
        gc.collect()
        free = gc.mem_free()
        return (str(free // 1024) + " KB free") if free >= 1024 else (str(free) + " B free")

    def _get_board(self):
        try:
            return machine.unique_id().hex()[:12]
        except:
            return "Pico W"

    def _get_cpu_speed(self):
        return str(machine.freq() // 1_000_000) + " MHz"

    def _page0_value(self, index):
        if index == 0: return "24h" if self.use_24h else "12h"
        if index == 1: return CPU_MODES[self.cpu_mode][0]
        if index == 2: return ""
        if index == 3: return "press I"
        return ""

    def _page1_value(self, index):
        if index == 0: return self._get_board()
        if index == 1: return self._get_ip()
        if index == 2: return self._get_ram()
        if index == 3: return self._get_cpu_speed()
        return ""

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_vol_bar(self, y, sel):
        d      = self.display
        bar_x  = 90
        bar_w  = 52
        bar_h  = 7
        bar_y  = y + 3
        fill_w = self.volume * bar_w // 100
        d.fillrect((bar_x, bar_y), (bar_w, bar_h), GREY)
        if fill_w > 0:
            col = RED if self.volume < 20 else (YELLOW if self.volume < 60 else GREEN)
            d.fillrect((bar_x, bar_y), (fill_w, bar_h), col)
        pct = str(self.volume) + "%"
        d.text((bar_x + bar_w + 3, y), pct, CYAN if sel else GREY, self.font, 1)

    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3),   "Settings", WHITE, self.font, 1)
        d.text((110, 3), "J:back",   GREY,  self.font, 1)

        for p in range(2):
            d.fillrect((74 + p * 8, 5), (4, 4), WHITE if p == self.page else GREY)

        d.fillrect((0, 116), (160, 12), TITLE_BG)
        if self.page == 1:
            d.text((4, 118), "A:back to settings", GREY, self.font, 1)
        elif self.cursor == 2:
            d.text((4, 118), "I:vol+  K:vol-  W/S:nav", GREY, self.font, 1)
        else:
            d.text((4, 118), "W/S:nav  I:sel  D:info", GREY, self.font, 1)

        if self._status and self.page == 0:
            sx = (160 - len(self._status) * 6) // 2
            d.text((sx, 106), self._status, self._status_color, self.font, 1)

        items = PAGE0 if self.page == 0 else PAGE1
        y = 22
        for i, label in enumerate(items):
            sel = (i == self.cursor) and (self.page == 0)
            if sel:
                d.fillrect((0, y - 1), (160, 13), SEL_BG)
                d.text((2, y), ">", CYAN, self.font, 1)
            d.text((12, y), label, CYAN if sel else WHITE, self.font, 1)
            if self.page == 0 and i == 2:
                self._draw_vol_bar(y, sel)
            else:
                val = self._page0_value(i) if self.page == 0 else self._page1_value(i)
                if val:
                    vx = 158 - len(val) * 6
                    d.text((vx, y), val, YELLOW if sel else GREY, self.font, 1)
            y += 18

    def _redraw_row(self, index):
        d   = self.display
        y   = 22 + index * 18
        sel = (index == self.cursor)
        d.fillrect((0, y - 1), (160, 13), SEL_BG if sel else BG)
        if sel:
            d.text((2, y), ">", CYAN, self.font, 1)
        d.text((12, y), PAGE0[index], CYAN if sel else WHITE, self.font, 1)
        if index == 2:
            self._draw_vol_bar(y, sel)
        else:
            val = self._page0_value(index)
            if val:
                vx = 158 - len(val) * 6
                d.text((vx, y), val, YELLOW if sel else GREY, self.font, 1)
        # Refresh footer when cursor lands on this row
        if index == self.cursor:
            d.fillrect((0, 116), (160, 12), TITLE_BG)
            if self.cursor == 2:
                d.text((4, 118), "I:vol+  K:vol-  W/S:nav", GREY, self.font, 1)
            else:
                d.text((4, 118), "W/S:nav  I:sel  D:info", GREY, self.font, 1)

    # ── volume helpers ────────────────────────────────────────────────────────

    def _vol_step(self):
        if self._vol_hold > 20: return 5
        if self._vol_hold > 8:  return 2
        return 1

    def _vol_up(self):
        self.volume = min(100, self.volume + self._vol_step())
        self._redraw_row(2)

    def _vol_down(self):
        self.volume = max(0, self.volume - self._vol_step())
        self._redraw_row(2)

    # ── input ─────────────────────────────────────────────────────────────────

    def handle_input(self, btns):
        if btns["J"].pressed():
            return "menu"

        if self.page == 0:
            # W/S always navigate regardless of row
            if btns["W"].pressed():
                prev = self.cursor
                self.cursor = (self.cursor - 1) % len(PAGE0)
                self._vol_hold = 0
                self._redraw_row(prev)
                self._redraw_row(self.cursor)

            elif btns["S"].pressed():
                prev = self.cursor
                self.cursor = (self.cursor + 1) % len(PAGE0)
                self._vol_hold = 0
                self._redraw_row(prev)
                self._redraw_row(self.cursor)

            elif btns["D"].pressed():
                self.page   = 1
                self.cursor = 0
                self._status = ""
                self._draw()

            elif self.cursor == 2:
                # Volume row — I/K held for adjustment with acceleration
                i_held = not btns["I"].pin.value()
                k_held = not btns["K"].pin.value()
                if i_held:
                    self._vol_hold += 1
                    self._vol_up()
                elif k_held:
                    self._vol_hold += 1
                    self._vol_down()
                else:
                    self._vol_hold = 0

            elif btns["I"].pressed():
                if self.cursor == 0:
                    self.use_24h = not self.use_24h
                    self._status = "24h on!" if self.use_24h else "12h on!"
                    self._status_color = GREEN
                    self._draw()

                elif self.cursor == 1:
                    self.cpu_mode = (self.cpu_mode + 1) % len(CPU_MODES)
                    name, freq = CPU_MODES[self.cpu_mode]
                    machine.freq(freq)
                    self._status = name + " " + str(freq // 1_000_000) + "MHz"
                    self._status_color = YELLOW if self.cpu_mode > 0 else GREEN
                    self._draw()

                elif self.cursor == 3:
                    if self.wifi_mgr:
                        self._status = "Syncing..."
                        self._status_color = YELLOW
                        self._draw()
                        try:
                            self.wifi_mgr.sync_time()
                            self._status = "Time synced!"
                            self._status_color = GREEN
                        except:
                            self._status = "Sync failed"
                            self._status_color = RED
                        self._draw()
                    else:
                        self._status = "No WiFi mgr"
                        self._status_color = RED
                        self._draw()

        else:
            if btns["A"].pressed():
                self.page   = 0
                self.cursor = 0
                self._draw()

        return None