import json
import threading
import time
from pynput.keyboard import Key, Controller

keyboard = Controller()
HELD_KEYS = set()
KEY_BEHAVIOR = {}

key_config_file = "key_config.json"

def get_key_object(key_str):
    if hasattr(Key, key_str):
        return getattr(Key, key_str)
    return key_str

def load_config(config_file_name):
    global KEY_BEHAVIOR
    try:
        with open(config_file_name, 'r') as f:
            raw_config = json.load(f)
            
        for move, behavior in raw_config.items():
            KEY_BEHAVIOR[move] = {
                "action": behavior["action"],
                "key": get_key_object(behavior["key"]),
                "duration": behavior.get("duration", 0.0) 
            }
    except FileNotFoundError:
        print("config file not found.")

load_config(key_config_file)

def delayed_release(key, delay):
    time.sleep(delay)
    keyboard.release(key)

def handle_cube_move(move_name):
    behavior = KEY_BEHAVIOR.get(move_name)

    if not behavior:
        return

    action = behavior["action"]
    key = behavior["key"]

    if action == "PRESS":
        if key not in HELD_KEYS:
            keyboard.press(key)
            HELD_KEYS.add(key)
    
    elif action == "RELEASE":
        if key in HELD_KEYS:
            keyboard.release(key)
            HELD_KEYS.remove(key)
            
    elif action == "CLICK":
        duration = behavior.get("duration", 0.0)
        keyboard.press(key)
        
        if duration > 0:
            threading.Thread(target=delayed_release, args=(key, duration), daemon=True).start()
        else:
            keyboard.release(key)
