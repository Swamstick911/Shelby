import time, math, struct, gc
from machine import I2S, Pin

NOTE = {"E5":659,"D5":587,"C5":523,"B4":494,"A4":440,"G4":392,"R":0}

audio = I2S(1, sck=Pin(10), ws=Pin(11), sd=Pin(9),
            mode=I2S.TX, bits=16, format=I2S.MONO,
            rate=24000, ibuf=4096)

buf = bytearray(512 * 2)

def play(freq, ms):
    samples = 24000 * ms // 1000
    done = 0
    phase = 0.0
    step = (2 * 3.14159 * freq / 24000) if freq > 0 else 0.0
    while done < samples:
        chunk = min(512, samples - done)
        for i in range(chunk):
            val = int(32767 * 0.3 * math.sin(phase)) if freq > 0 else 0
            struct.pack_into("<h", buf, i*2, val)
            phase += step
            if phase > 6.2832: phase -= 6.2832
        audio.write(memoryview(buf)[:chunk*2])
        done += chunk

print("playing...")
play(NOTE["E5"], 250)
play(NOTE["D5"], 250)
play(NOTE["C5"], 250)
play(NOTE["E5"], 500)
print("done")
audio.deinit()