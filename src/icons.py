def draw_github(display, x, y, color):
    # Head outline — 4 lines instead of rect
    display.line((x+4, y+8),  (x+20, y+8),  color)  # top
    display.line((x+4, y+20), (x+20, y+20), color)  # bottom
    display.line((x+4, y+8),  (x+4,  y+20), color)  # left
    display.line((x+20,y+8),  (x+20, y+20), color)  # right
    # Ears
    display.line((x+4,  y+8), (x+4,  y+2), color)
    display.line((x+4,  y+2), (x+8,  y+8), color)
    display.line((x+20, y+8), (x+20, y+2), color)
    display.line((x+20, y+2), (x+16, y+8), color)
    # Whiskers
    display.line((x,    y+12), (x+3,  y+12), color)
    display.line((x+21, y+12), (x+24, y+12), color)
    display.line((x,    y+16), (x+3,  y+16), color)
    display.line((x+21, y+16), (x+24, y+16), color)
    # Eyes
    display.fillrect((x+8,  y+12), (2, 2), color)
    display.fillrect((x+14, y+12), (2, 2), color)


def draw_gmail(display, x, y, color):
    # Envelope body
    display.line((x+2,  y+5),  (x+22, y+5),  color)  # top
    display.line((x+2,  y+19), (x+22, y+19), color)  # bottom
    display.line((x+2,  y+5),  (x+2,  y+19), color)  # left
    display.line((x+22, y+5),  (x+22, y+19), color)  # right
    # Flap V
    display.line((x+2,  y+5),  (x+12, y+12), color)
    display.line((x+22, y+5),  (x+12, y+12), color)
    # Bottom fold lines
    display.line((x+2,  y+19), (x+8,  y+14), color)
    display.line((x+22, y+19), (x+16, y+14), color)


def draw_tasks(display, x, y, color):
    # Clipboard body
    display.line((x+4,  y+2),  (x+18, y+2),  color)  # top
    display.line((x+4,  y+22), (x+18, y+22), color)  # bottom
    display.line((x+4,  y+2),  (x+4,  y+22), color)  # left
    display.line((x+18, y+2),  (x+18, y+22), color)  # right
    # Clip at top
    display.fillrect((x+8, y), (6, 4), color)
    # Checkmark (double thickness)
    display.line((x+7,  y+12), (x+11, y+16), color)
    display.line((x+7,  y+13), (x+11, y+17), color)
    display.line((x+11, y+16), (x+17, y+8),  color)
    display.line((x+11, y+17), (x+17, y+9),  color)


def draw_settings(display, x, y, color):
    # Inner hole
    display.line((x+10, y+10), (x+14, y+10), color)
    display.line((x+10, y+14), (x+14, y+14), color)
    display.line((x+10, y+10), (x+10, y+14), color)
    display.line((x+14, y+10), (x+14, y+14), color)
    # Gear body
    display.line((x+8,  y+8),  (x+16, y+8),  color)
    display.line((x+8,  y+16), (x+16, y+16), color)
    display.line((x+8,  y+8),  (x+8,  y+16), color)
    display.line((x+16, y+8),  (x+16, y+16), color)
    # 4 spokes
    display.fillrect((x+10, y+4),  (4, 4), color)
    display.fillrect((x+10, y+16), (4, 4), color)
    display.fillrect((x+4,  y+10), (4, 4), color)
    display.fillrect((x+16, y+10), (4, 4), color)
    # 4 diagonal corners
    display.fillrect((x+6,  y+6),  (2, 2), color)
    display.fillrect((x+16, y+6),  (2, 2), color)
    display.fillrect((x+6,  y+16), (2, 2), color)
    display.fillrect((x+16, y+16), (2, 2), color)


def draw_hackatime(display, x, y, color):
    """Clock face with a lightning bolt — coding time tracker."""
    # Clock circle (outline)
    display.line((x+4,  y),    (x+20, y),    color)  # top
    display.line((x+4,  y+20), (x+20, y+20), color)  # bottom
    display.line((x,    y+4),  (x,    y+16), color)  # left
    display.line((x+24, y+4),  (x+24, y+16), color)  # right
    # Clock hands
    display.line((x+12, y+4),  (x+12, y+12), color)  # hour hand up
    display.line((x+12, y+12), (x+18, y+12), color)  # minute hand right
    # Lightning bolt (coding = energy)
    display.line((x+14, y+14), (x+10, y+20), color)
    display.line((x+10, y+20), (x+13, y+20), color)
    display.line((x+13, y+20), (x+9,  y+24), color)


def draw_music(display, x, y, color):
    """Music note — filled note head with stem and flag."""
    # Note head (filled oval approximated with rects)
    display.fillrect((x+4,  y+16), (6, 4), color)  # main body
    display.fillrect((x+3,  y+17), (8, 2), color)  # wider middle
    # Stem (right side of head, going up)
    display.line((x+10, y+4), (x+10, y+18), color)
    # Flag on stem
    display.line((x+10, y+4),  (x+16, y+7),  color)  # flag top
    display.line((x+10, y+8),  (x+16, y+11), color)  # flag bottom curve
    display.line((x+16, y+7),  (x+16, y+11), color)  # flag right edge

def draw_games(display, x, y, color):
    """Gamepad icon"""
    #Outer controller body
    display.line((x+2, y+6), (x+22, y+6), color)
    display.line((x+2, y+18), (x+22, y+18), color)
    display.line((x+2, y+6), (x+2, y+18), color)
    display.line((x+22, y+6), (x+22, y+18), color)

    #Left side
    display.fillrect((x+6, y+11), (4, 2), color)
    display.fillrect((x+7, y+10), (2, 4), color)

    #right side
    display.fillrect((x+15, y+13), (2, 2), color)
    display.fillrect((x+18, y+10), (2, 2), color)

    #Middle
    display.line((x+11, y+16), (x+13, y+14), color)
    display.line((x+8, y+16), (x+10, y+14), color)