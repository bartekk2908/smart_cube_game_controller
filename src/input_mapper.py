from pynput.keyboard import Key, Controller


keyboard = Controller()

HELD_KEYS = set()

KEY_BEHAVIOR = {
    "R":  {"action": "PRESS", "key": "d"},
    "R'": {"action": "RELEASE", "key": "d"},

    "L": {"action": "RELEASE", "key": "a"},
    "L'":  {"action": "PRESS", "key": "a"},

    "U":  {"action": "CLICK", "key": Key.space},
    "U'":  {"action": "CLICK", "key": Key.space},

    "D":  {"action": "CLICK", "key": Key.down},
    "D'":  {"action": "CLICK", "key": Key.down},

    "F":  {"action": "PRESS", "key": Key.ctrl_r},
    "F'":  {"action": "RELEASE", "key": Key.ctrl_r},

    "B":  {"action": "RELEASE", "key": Key.shift_r},
    "B'":  {"action": "PRESS", "key": Key.shift_r},
}

def handle_cube_move(move_name):
    behavior = KEY_BEHAVIOR.get(move_name)

    if not behavior:
        return

    action = behavior["action"]
    key = behavior["key"]

    if action == "PRESS":
        if key not in HELD_KEYS:
            # print(f"  [Keyboard] Holding down: {key}")
            keyboard.press(key)
            HELD_KEYS.add(key)
    
    elif action == "RELEASE":
        if key in HELD_KEYS:
            # print(f"  [Keyboard] Releasing: {key}")
            keyboard.release(key)
            HELD_KEYS.remove(key)
            
    elif action == "CLICK":
        # print(f"  [Keyboard] Clicking: {key}")
        keyboard.press(key)
        keyboard.release(key)
