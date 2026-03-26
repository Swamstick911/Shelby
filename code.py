import time
import board
import displayio
import keypad

try:
    from secrets import secrets
except ImportError:
    print("ERROR: secrets.py not found.")
    while True: time.sleep(1)

# Init hardware
display = board.DISPLAY
BUTTONS = (board.W, board.A, board.S, board.D, board.I, board.J, board.K, board.L)
keys = keypad.Keys(BUTTONS, value_when_pressed=False, pull=True)

# Boot screen
boot_group = displayio.Group()
display.root_group = boot_group

# Connect to network
from src.wifi_manager import WifiManager
wifi_mgr = WifiManager(secrets)
wifi_connected = wifi_mgr.connect()
if wifi_connected:
    wifi_mgr.sync_time()

# Load our views
from src.clock import ClockScreen
from src.github import GitHubScreen
from src.gmail import GmailScreen
from src.tasks import TaskScreen

clock_screen = ClockScreen(display.width, display.height)
gh_screen = GitHubScreen(display.width, display.height, wifi_mgr.requests, secrets.get("github_token"))
gmail_screen = GmailScreen(display.width, display.height, wifi_mgr.requests, secrets.get("gmail_token"))
tasks_screen = TaskScreen(display.width, display.height)

# State
MENU_ITEMS = ["Clock", "GitHub", "Gmail", "Tasks"]
menu_index = 0
current_view = "Clock"
display.root_group = clock_screen

print("Shelby OS Started.")

# First fetch to populate badges on boot
if wifi_connected:
    gh_screen.fetch()
    gmail_screen.fetch()

clock_screen.show_menu_hint(menu_index, gh_screen.unread_count, gmail_screen.unread_count)

# Polling timer for background fetches
last_api_fetch = time.monotonic()

while True:
    # 1. Background Updates
    if current_view == "Clock":
        clock_screen.update()
        
    # Refresh APIs every 5 minutes in the background
    if time.monotonic() - last_api_fetch > 300:
        if wifi_connected:
            gh_screen.fetch()
            gmail_screen.fetch()
            clock_screen.show_menu_hint(menu_index, gh_screen.unread_count, gmail_screen.unread_count)
        last_api_fetch = time.monotonic()

    # 2. Key Handling
    event = keys.events.get()
    if event and event.pressed:
        key_pin = BUTTONS[event.key_number]
        
        if key_pin == board.A:
            # Global Back
            current_view = "Clock"
            menu_index = 0
            display.root_group = clock_screen
            clock_screen.show_menu_hint(menu_index, gh_screen.unread_count, gmail_screen.unread_count)
            
        elif current_view == "Clock":
            # Navigating the home menu
            if key_pin == board.W:
                menu_index = (menu_index - 1) % len(MENU_ITEMS)
                clock_screen.show_menu_hint(menu_index, gh_screen.unread_count, gmail_screen.unread_count)
            elif key_pin == board.S:
                menu_index = (menu_index + 1) % len(MENU_ITEMS)
                clock_screen.show_menu_hint(menu_index, gh_screen.unread_count, gmail_screen.unread_count)
            elif key_pin == board.D:
                current_view = MENU_ITEMS[menu_index]
                if current_view == "GitHub":
                    display.root_group = gh_screen
                    gh_screen.fetch() # Refresh on enter
                elif current_view == "Gmail":
                    display.root_group = gmail_screen
                    gmail_screen.fetch()
                elif current_view == "Tasks":
                    display.root_group = tasks_screen
                    tasks_screen.fetch()
        elif current_view == "Tasks":
            # Task specific controls
            if key_pin == board.W:
                tasks_screen.move_cursor(-1)
            elif key_pin == board.S:
                tasks_screen.move_cursor(1)
            elif key_pin == board.D:
                tasks_screen.toggle_task()
            elif key_pin == board.L:
                tasks_screen.delete_task()

    time.sleep(0.01)