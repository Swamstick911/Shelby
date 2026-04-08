import st7735
import math
import struct
import gc
from machine import I2S, Pin
from src.songs import SONGS 

def _c(r, g, b):
    return((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BG = st7735.TFT.BLACK
WHITE = st7735.TFT.WHITE
GREEN = st7735.TFT.GREEN
RED = st7735.TFT.RED
CYAN = st7735.TFT.CYAN
YELLOW = _c(255, 220, 0)
GREY = _c(120, 120, 120)
PURPLE = _c(180, 100, 255)
TITLE_BG = _c(10, 10, 30)
SEL_BG = _c(20, 40, 20)

#Sprig I2S pins (from HAL.C)
_I2S_BCLK = 27
_I2S_LRCLK =  28
_I2S_DATA = 26
_SAMPLE_RATE = 24000
_VOLUME = 0.4

class MusicScreen:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.cursor = 0
        self.playing = False
        self.paused = False
        self._audio = None
        self._stop = False

    def show(self):
        self._stop = False
        self.playing = False
        self.paused = False
        self._draw()

    #I2S init/deinit

    def _init_audio(self):
        if self._audio is None:
            gc.collect()
            self._audio = I2S(
                0,
                sck=Pin(_I2S_BCLK),
                ws=Pin(_I2S_LRCLK),
                sd=Pin(_I2S_DATA),
                mode=I2S.TX,
                bits=16,
                format=I2S.MONO,
                rate=_SAMPLE_RATE,
                ibuf=4096,
            )
    
    def _deinit_audio(self):
        if self._audio is not None:
            self._audio.deinit()
            self._audio = None
            gc.collect()

    #Tone generation
    def _play_tone(self, freq, duration_ms):
        """Generate and write a single tone (or rest) to I2S"""
        samples = _SAMPLE_RATE * duration_ms // 1000
        if samples == 0:
            return
        buf = bytearray(samples * 2)
        if freq > 0:
            step = 2 * math.pi * freq / _SAMPLE_RATE
            for i in range(samples):
                val = int(32767 * _VOLUME * math.sin(step * i))
                struct.pack_into("<h", buf, i * 2, val)
        #buf stays all zeros for REST
        self._audio.write(buf)

    def _play_song(self, index):
        """Play song at index, stops if self._stop is set"""
        self._init_audio()
        song = SONGS[index]
        self.playing = True
        self.paused = False
        self._draw_status()

        try:
            for freq, dur in song["data"]:
                if self._stop:
                    break
                self._play_tone(freq, dur)
        except Exception as e:
            print("Audio error:", e)

        self.playing = False
        self._deinit_audio()
        if not self._stop:
            #Song finished naturally
            self._draw_status()

    
    #Drawing

    def _draw(self):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Music", WHITE, self.font, 1)
        d.text((104, 3), "J:back", GREY, self.font, 1)

        #Footer
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((4, 118), "W/S:nav  I:play    K:stop", GREY, self.font, 1)

        #Song list
        y = 18
        for i, song in enumerate(SONGS):
            sel = (i == self.cursor)
            if sel:
                d.fillrect((0, y - 1), (160, 13), SEL_BG)
                d.text((2, y), ">", CYAN, self.font, 1)
            lc = CYAN if sel else WHITE
            d.text((12, y), song["title"][:20], lc, self.font, 1)
            y += 14

        #Footer
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((4, 118), "W/S:nav   I:nav    J:back", GREY, self.font, 1)

    def _draw_playing(self, title):
        d = self.display
        d.fill(BG)
        d.fillrect((0, 0), (160, 14), TITLE_BG)
        d.text((8, 3), "Music", WHITE, self.font, 1)
        d.text((110, 3), "J:stop", GREY< self.font, 1)
        d.text((8, 35), "Now playing", GREY, self.font, 1)
        d.text((8, 50), title[:20], YELLOW, self.font, 1)
        #Animated note symbols
        d.text((20, 75), " >> ", GREEN, self.font, 2)
        d.fillrect((0, 116), (160, 12), TITLE_BG)
        d.text((40, 118), "J:stop", GREY, self.font, 1)

    def hamdle_input(self, btns):
        if self.playing:
            #While playing only J button stops it
            if btns["J"].pressed():
                self._stop = True
                self.playing = False
                self._deinit_audio()
                self._draw()
            return None
        
        if btns["J"].pressed():
            self._deinit_audio()
            return "menu"
        
        if btns["W"].pressed():
            self.cursor = (self.cursor - 1) % len(SONGS)
            self._draw()

        elif btns["S"].pressed():
            self.cursor = (self.cursor + 1) % len(SONGS)
            self._draw()

        elif btns["I"].pressed():
            self.playing = True
            self._stop = False
            self._play_song(self.cursor)

        return None