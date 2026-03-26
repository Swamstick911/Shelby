import time
import board
import displayio
import keypad

# Attempt to load secrets early
try:
    from secrets import secrets
except ImportError:
    print("ERROR: secrets.py not found. Please copy secrets.py.example to secrets.py")
    while True: time.sleep(1)

# Initialize Sprig Display
display = board.DISPLAY

# Initialize Sprig Buttons using the correct 'BUTTON_' prefixes
BUTTONS = (board.BUTTON_W, board.BUTTON_A, board.BUTTON_S, board.BUTTON_D, 
           board.BUTTON_I, board.BUTTON_J, board.BUTTON_K, board.BUTTON_L)

keys = keypad.Keys(BUTTONS, value_when_pressed=False, pull=True)

# Import our custom screens
from src.clock import ClockScreen

# Initialize screens
clock_screen = ClockScreen(display.width, display.height)
display.root_group = clock_screen

# Navigation State
MENU_ITEMS = ["Clock", "GitHub", "Gmail", "Tasks"]
menu_index = 0
current_view = "Clock" 

# Initial screen setup
clock_screen.show_menu_hint(menu_index)
print("Shelby OS Starting...")

while True:
    # Update active screen
    if current_view == "Clock":
        clock_screen.update()
        
    # Handle physical buttons
    event = keys.events.get()
    if event and event.pressed:
        key_pin = BUTTONS[event.key_number]
        
        if key_pin == board.BUTTON_W:
            # Scroll left/up in menu
            menu_index = (menu_index - 1) % len(MENU_ITEMS)
            if current_view == "Clock":
                clock_screen.show_menu_hint(menu_index)
                
        elif key_pin == board.BUTTON_S:
            # Scroll right/down in menu
            menu_index = (menu_index + 1) % len(MENU_ITEMS)
            if current_view == "Clock":
                clock_screen.show_menu_hint(menu_index)
                
        elif key_pin == board.BUTTON_D:
            # Enter selected screen
            selected = MENU_ITEMS[menu_index]
            if selected != current_view:
                print(f"Entering {selected} screen... (Stub)")
                current_view = selected
                
        elif key_pin == board.BUTTON_A:
            # Always go back to Home/Clock
            if current_view != "Clock":
                print("Returning to Home screen")
                current_view = "Clock"
                menu_index = 0
                display.root_group = clock_screen
                clock_screen.show_menu_hint(menu_index)
                
    time.sleep(0.02) 