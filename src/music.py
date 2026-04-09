import st7735
import gc
import time
import math
import struct
from machine import I2S, Pin, SPI
from src.songs import SONGS


def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BG       = st7735.TFT.BLACK
WHITE    = st7735.TFT.WHITE
GREEN    = st7735.TFT.GREEN
CYAN     = st7735.TFT.CYAN
YELLOW   = _c(255, 220, 0)
GREY     = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)
SEL_BG   = _c(20, 40, 20)

_I2S_BCLK    = 10
_I2S_LRCLK   = 11
_I2S_DATA    = 9
_SAMPLE_RATE = 24000
_VOLUME      = 0.3
_CHUNK       = 512


def _reinit_display(display):
    spi = SPI(0, baudrate=8000000, polarity=0, phase=0,
              sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    display.spi   = spi
    display.dc    = Pin(22, Pin.OUT, Pin.PULL_DOWN)
    display.reset = Pin(26, Pin.OUT, Pin.PULL_DOWN)
    display.cs    = Pin(20, Pin.OUT, Pin.PULL_DOWN)
    display.cs(1)
    display.initg()
    display.rgb(False)
    display.rotation(1)


class MusicScreen:
    def __init__(self, display, font):
        self.display   = display
        self.font      = font
        self.cursor    = 0
        self.playing   = False
        self._song_idx = 0
        self._buf      = bytearray(_CHUNK * 2)

    def show(self):
        self.playing = False
        self._draw()

    def _play_tone(self, audio, freq, duration_ms):
        total_samples = _SAMPLE_RATE * duration_ms // 1000
        if total_samples == 0:
            return
        done = 0
        phase = 0.0
        step = (2 * math.pi * freq / _SAMPLE_RATE) if freq > 0 else 0.0
        while done < total_samples:
            chunk = min(_CHUNK, total_samples - done)
            for i in range(chunk):
                if freq > 0:
                    val = int(32767 * _VOLUME * math.sin(phase))
                    phase += step
                    if phase > 6.2832:
                        phase -= 6.2832
                else:
                    val = 0
                struct.pack_into("<h", self._buf, i * 2, val)
            audio.write(memoryview(self._buf)[:chunk * 2])
            done += chunk

    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3),   "Music",  WHITE, self.font, 1)
        d.text((100, 3), "J:back", GREY,  self.font, 1)
        y = 20
        for i, song in enumerate(SONGS):
            sel = (i == self.cursor)
            if sel:
                d.fillrect((0, y - 1), (160, 13), SEL_BG)
                d.text((4, y), ">", CYAN, self.font, 1)
            d.text((12, y), song["title"][:20], CYAN if sel else WHITE, self.font, 1)
            y += 14
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((4, 118), "W/S:nav  I:play  J:back", GREY, self.font, 1)

    def handle_input(self, btns):
        if self.playing:
            return None

        if btns["J"].pressed():
            return "menu"

        if btns["W"].pressed():
            self.cursor = (self.cursor - 1) % len(SONGS)
            self._draw()
        elif btns["S"].pressed():
            self.cursor = (self.cursor + 1) % len(SONGS)
            self._draw()
        elif btns["I"].pressed():
            song = SONGS[self.cursor]
            self._song_idx = self.cursor
            d = self.display

            # 1. Draw "Now Playing"
            d.fill(BG)
            d.fillrect((0, 0), (160, 14), TITLE_BG)
            d.text((8,  3),  "Music",           WHITE,  self.font, 1)
            d.text((8,  28), "Now playing",      GREY,   self.font, 1)
            d.text((8,  44), song["title"][:20], YELLOW, self.font, 1)
            d.text((35, 72), ">>  <<",           GREEN,  self.font, 2)
            d.fillrect((0, 116), (160, 12), TITLE_BG)
            d.text((15, 118), "Playing...", GREY, self.font, 1)

            # 2. Put display into hardware sleep — freezes framebuffer,
            #    ST7735 ignores all pin activity while sleeping
            d._writecommand(0x10)  # SLPIN
            d.cs(1)
            time.sleep_ms(120)     # ST7735 datasheet: 120ms to enter sleep

            # 3. Init I2S on PIO1 (SPI0 uses PIO0 — no conflict)
            gc.collect()
            audio = I2S(
                1,
                sck=Pin(_I2S_BCLK),
                ws=Pin(_I2S_LRCLK),
                sd=Pin(_I2S_DATA),
                mode=I2S.TX,
                bits=16,
                format=I2S.MONO,
                rate=_SAMPLE_RATE,
                ibuf=4096,
            )
            self.playing = True

            # 4. Play entire song
            for freq, dur in song["data"]:
                self._play_tone(audio, freq, dur)

            # 5. Deinit I2S
            audio.deinit()
            del audio
            gc.collect()
            self.playing = False

            # 6. Reinit SPI + wake display
            _reinit_display(self.display)   # initg() already handles SLPOUT + DISPON
            self._draw()

        return None