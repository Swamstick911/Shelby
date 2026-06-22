def draw_char_on_bg(display, font, ch, x, y, fg, bg):
    """draw a single character with expicit bg color"""
    ci = ord(ch)
    if not (font["Start"] <= ci <= font ["End"]):
        return
    fontw = font["Width"]
    fonth = font["Height"]
    ci = (ci -font["Start"]) * fontw
    charA = font["Data"][ci:ci + fontw]
    for col in range(fontw):
        c = charA[col]
        for row in range(fonth):
            color = fg if (c & 0x01) else bg
            display.pixel((x + col, y + row), color)
            c >>= 1

def draw_text_on_bg(display, font, text, x, y, fg, bg):
    """Draw a full string with explicit bg color at scale=1"""
    px = x
    for ch in text:
        draw_char_on_bg(display, font, ch, px, y, fg, bg)
        px += font["Width"] + 1