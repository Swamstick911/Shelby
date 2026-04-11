import st7735
import gc
import time
import math
import struct
import array
import micropython
from machine import I2S, Pin, SPI
from src.songs import SONGS


def _c(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
CYAN = st7735.TFT.CYAN
YELLOW = _c(255, 220, 0)
GREY = _c(120, 120, 120)
TITLE_BG = _c(10, 10, 30)
SEL_BG = _c(20, 40, 20)

_I2S_BCLK = 10
_I2S_LRCLK = 11
_I2S_DATA = 9
_SAMPLE_RATE = 11025
_VOLUME = 0.5
_CHUNK = 512

# Pre-computed wavetable
_WAVE_SIZE = 256
_WAVETABLE = array.array('h', [
    int(32767 * math.sin(2 * math.pi * i / _WAVE_SIZE))
    for i in range(_WAVE_SIZE)
])


class MusicScreen:
    def __init__(self, display, font, settings):
        self.display = display
        self.font = font
        self.settings = settings
        self.cursor = 0
        self.playing = False
        self._song_idx = 0
        self._buf = bytearray(_CHUNK * 2)  
        self._sil = bytearray(2048)

    def show(self):
        self.playing = False
        self._draw()
        
    @micropython.native
    def _play_tone(self, audio, freq, duration_ms, phase_idx=0.0):
        total_samples = _SAMPLE_RATE * duration_ms // 1000
        if total_samples == 0:
            return phase_idx
        done = 0
        step = (freq * _WAVE_SIZE / _SAMPLE_RATE) if freq > 0 else 0.0
        vol = self.settings.volume / 100.0
        wt = _WAVETABLE
        mask = _WAVE_SIZE - 1
        buf = self._buf
        while done < total_samples:
            chunk = min(_CHUNK, total_samples - done)
            if freq > 0:
                for i in range(chunk):
                    val = int(wt[int(phase_idx) & mask] * vol)
                    buf[i * 2]     = val & 0xFF
                    buf[i * 2 + 1] = (val >> 8) & 0xFF
                    phase_idx += step
                    if phase_idx >= _WAVE_SIZE:
                        phase_idx -= _WAVE_SIZE
            else:
                #silence, zero the buffer slice directly
                for i in range(chunk * 2):
                    buf[i] = 0
            audio.write(memoryview(buf)[:chunk * 2])
            done += chunk
        return phase_idx

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

    def _draw_playing(self, title):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8,  3),  "Music",       WHITE,  self.font, 1)
        d.text((8,  28), "Now playing", GREY,   self.font, 1)
        d.text((8,  44), title[:20],    YELLOW, self.font, 1)
        d.text((35, 72), ">>  <<",      GREEN,  self.font, 2)
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((15, 118), "Playing...", GREY, self.font, 1)

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

            # 1. Draw now playing
            self._draw_playing(song["title"])

            # 2. Init I2S
            gc.collect()
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
                ibuf=8192,  # larger internal buffer = more headroom
            )

            # 3. Flush silence
            audio.write(self._sil)
            self.playing = True

            # 4. Play
            phase = 0.0
            for freq, dur in song["data"]:
                phase = self._play_tone(audio, freq, dur, phase)

            # 5. Flush silence and drain before deinit
            audio.write(self._sil)
            time.sleep_ms(200)
            audio.deinit()
            del audio
            gc.collect()
            self.playing = False

            # 6. Redraw
            self._draw()

        return None