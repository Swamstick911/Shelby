def draw_github(display, x, y, color):
    """Draws a minimalist Github logo"""
    #Head outline
    display.rect(x + 4, y + 8, 16, 12, color)

    #Ears
    display.line(x + 4, y + 8, x + 4, y + 2, color)
    display.line(x + 4, y + 2, x + 8, y + 8, color)
    display.line(x + 20, y + 8, x + 20, y + 2, color)
    display.line(x + 20, y + 2, x + 16, y + 8, color)

    #Whiskers
    display.hline(x, y + 12, 3, color)
    display.hline(x + 21, y + 12, 3, color)
    display.hline(x, y + 16, 3, color)
    display.hline(x + 21, y + 16, 3, color)

def draw_gmail(display, x, y, color):
    """Draws the classic small enevelope logo"""
    #Main body
    display.rect(x + 2, y + 5, 20, 14, color)

    #Top flap
    display.line(x + 2, y + 5, x + 12, y + 12, color)
    display.line(x + 22, y + 5, x + 12, y + 12, color)

    #Bottom
    display.line(x + 2, y + 19, x + 8, y + 14, color)
    display.line(x + 22, y + 19, x + 16, y + 14, color)

def draw_tasks(display, x, y, color):
    """Draws clipboard with a checkmark"""
    #Clipboard board
    display.rect(x + 4, y + 2, 14, 20, color)
    #Clipboard clip
    display.fill_rect(x + 8, y, 6, 4, color)

    #Bold Checkmark
    display.line(x + 7, y + 12, x + 11, y + 16, color)
    display.line(x + 7, y + 13, x + 11, y + 17, color) #Double thickness

    display.line(x + 11, y + 16, x + 17, y + 8, color)
    display.line(x + 11, y + 17, x + 17, y + 9, color) # Double thickness

def _draw_settings(display, x, y, color):
    """Draws a mechanical gear"""
    #Inner empty hole
    display.rect(x + 10, y + 10, 4, 4, color)
    #Main gear body
    display.rect(x + 8, y + 8, 8, 8, color)

    #4 straight spokes
    display.fill_rect(x + 10, y + 4, 4, 4, color)
    display.fill_rect(x + 10, y + 16, 4, 4, color)
    display.fill_rect(x + 4, y + 10, 4, 4, color)
    display.fill_rect(x + 16, y + 10, 4, 4, color)

    #4 diagonal spokes
    display.fill_rect(x + 6, y + 6, 2, 2, color)
    display.fill_rect(x + 16, y + 6, 2, 2, color)
    display.fill_rect(x + 6, y + 16, 2, 2, color)
    display.fill_rect(x + 16, y + 16, 2, 2, color)
    