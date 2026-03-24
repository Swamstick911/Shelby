import time
import board
import displayio
import keyboard

try:
    from secrets import secrets
except ImportError:
    print("ERROR: secrets.py not found. Please copy secrets.py.example to secrets.py")
    while True:
        time.sleep(1)

# display initialisation
display = board.DISPLAY

# buttons initialisation
BUTTONS = (board.W, board.A, board.S, board.D, board.I, board.J, board.K, board.L)
keys = keypad.Keys(BUTTONS, value_when_pressed=False, pull=True)

#Import custom screens
from src.clock import ClockScreen

#Initialise screens
clock_screen =  ClockScreen(display.width, display.height)
display.root_group = clock_screen

#Navigation state
MENU_ITEMS = ["Clock", "Github", "Gmail", "Tasks"]
menu_index = 0
current_view = "Clock"

#Initial Screen setup
clock_screen.show_menu_hint(menu_index)
print("Shelby OS Starting...")

while True:
    # Update the active screen
    if current_view == "Clock":
        clock_screen.update()

    #Handle physical buttons
    event = keys.events.get()
    if event and event.pressed:
        key_pin = BUTTONS[event.key_number]

        if key_pin == board.W:
            #Scroll up/left in menu
            menu_index = (menu_index - 1) % len(MENU_ITEMS)
            if current_view == "Clock":
                clock_screen.show_menu_hint(menu_index)

        elif key_pin == board.S:
            #Scroll down/right in menu
            menu_index = (menu_index + 1) % len(MENU_ITEMS)
            if current_view == "Clock":
                clock_screen.show_menu_hint(menu_index)
        
        elif key_pin == board.D:
            #Enter selected screen
            selected = MENU_ITEMS[menu_index]
            if selected != current_view:
                print (f"Entering {selected} screen... (Stub)")
                #TODO:Switch display.root_group once other modules are ready
                current_view = selected
        
        elif key_pin == board.A:
            #Always go back to Home/Clock screen
            if current_view != "Clock":
                print("Returning to Home screen...")
                current_view = "Clock"
                menu_index = 0
                display.root_group = clock_screen
                clock_screen.show_menu_hint(menu_index)

    time.sleep(0.02)
