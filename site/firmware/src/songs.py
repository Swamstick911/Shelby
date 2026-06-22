NOTE = {
    "C4": 261, "D4": 294, "E4": 330, "F4": 349,
    "G4": 392, "A4": 440, "B4": 494,
    "C5": 523, "D5": 587, "E5": 659, "F5": 698,
    "G5": 784, "A5": 880, "B5": 988,
    "C3": 131, "D3": 147, "E3": 165, "G3": 196, "A3": 220, "B3": 247,
    "R":  0,   # Rest
}

# Each song is a list of (freq_hz, duration_ms) tuples
# Duration: 500=half, 250=quarter, 125=eighth note at ~120bpm

SONGS = [
    {
        "title": "Tetris",
        "data": [
            (NOTE["E5"], 250), (NOTE["B4"], 125), (NOTE["C5"], 125),
            (NOTE["D5"], 250), (NOTE["C5"], 125), (NOTE["B4"], 125),
            (NOTE["A4"], 250), (NOTE["A4"], 125), (NOTE["C5"], 125),
            (NOTE["E5"], 250), (NOTE["D5"], 125), (NOTE["C5"], 125),
            (NOTE["B4"], 375), (NOTE["C5"], 125),
            (NOTE["D5"], 250), (NOTE["E5"], 250),
            (NOTE["C5"], 250), (NOTE["A4"], 250),
            (NOTE["A4"], 500),
            (NOTE["R"],  125),
            (NOTE["D5"], 250), (NOTE["F5"], 125), (NOTE["A5"], 250),
            (NOTE["G5"], 125), (NOTE["F5"], 125),
            (NOTE["E5"], 375), (NOTE["C5"], 125),
            (NOTE["E5"], 250), (NOTE["D5"], 125), (NOTE["C5"], 125),
            (NOTE["B4"], 375), (NOTE["C5"], 125),
            (NOTE["D5"], 250), (NOTE["E5"], 250),
            (NOTE["C5"], 250), (NOTE["A4"], 250),
            (NOTE["A4"], 500),
        ]
    },
    {
        "title": "Mario Theme",
        "data": [
            (NOTE["E5"], 125), (NOTE["E5"], 125), (NOTE["R"],  125),
            (NOTE["E5"], 125), (NOTE["R"],  125), (NOTE["C5"], 125),
            (NOTE["E5"], 250), (NOTE["G5"], 250),
            (NOTE["R"],  250), (NOTE["G4"], 250),
            (NOTE["R"],  250),
            (NOTE["C5"], 250), (NOTE["R"],  125), (NOTE["G4"], 250),
            (NOTE["R"],  125), (NOTE["E4"], 250),
            (NOTE["R"],  125), (NOTE["A4"], 250), (NOTE["R"],  125),
            (NOTE["B4"], 250), (NOTE["R"],  125), (NOTE["A4"] - 10, 250),
            (NOTE["A4"] - 20, 125), (NOTE["G4"], 167),
            (NOTE["E5"], 167), (NOTE["G5"], 167),
            (NOTE["A5"], 250), (NOTE["F5"], 125), (NOTE["G5"], 125),
            (NOTE["R"],  125), (NOTE["E5"], 250),
            (NOTE["C5"], 125), (NOTE["D5"], 125), (NOTE["B4"], 250),
        ]
    },
    {
        "title": "Zelda Lullaby",
        "data": [
            (NOTE["B4"], 375), (NOTE["D5"], 125), (NOTE["A4"], 250),
            (NOTE["R"],  125), (NOTE["B4"], 125), (NOTE["R"],  125),
            (NOTE["E5"], 500),
            (NOTE["B4"], 375), (NOTE["D5"], 125), (NOTE["A4"], 375),
            (NOTE["G5"], 500),
            (NOTE["B4"], 375), (NOTE["D5"], 125), (NOTE["A4"], 250),
            (NOTE["B4"], 250), (NOTE["E5"], 500),
            (NOTE["D5"], 375), (NOTE["F5"], 125), (NOTE["C5"], 375),
            (NOTE["B4"], 500),
        ]
    },
    {
        "title": "Never Gonna",
        "data": [
            (NOTE["A4"], 125), (NOTE["B4"], 125), (NOTE["D5"], 250),
            (NOTE["B4"], 125), (NOTE["D5"], 125), (NOTE["E5"], 125),
            (NOTE["R"],  125), (NOTE["A4"], 125), (NOTE["B4"], 125),
            (NOTE["D5"], 250), (NOTE["B4"], 125), (NOTE["E5"], 250),
            (NOTE["R"],  125), (NOTE["A4"], 125), (NOTE["B4"], 125),
            (NOTE["D5"], 250), (NOTE["B4"], 125), (NOTE["F5"], 250),
            (NOTE["E5"], 375),
            (NOTE["A4"], 125), (NOTE["B4"], 125), (NOTE["D5"], 250),
            (NOTE["B4"], 125), (NOTE["E5"], 250), (NOTE["R"],  125),
            (NOTE["G5"], 125), (NOTE["E5"], 250), (NOTE["D5"], 375),
        ]
    },
]