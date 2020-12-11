#!/usr/bin/env python3

# Imports {{{
# builtins
from string import ascii_letters
from threading import Thread
from queue import Queue

# 3rd party
import keyboard

# local modules
from .utils import restart

# }}}


def shift(char):
    """
    Smarter version of the letter-case calculation in the
    keyboard.get_typed_string() function. I use this in my own
    get_typed_string_f() function because keyboard wasn't properly reading
    'shift' + ';' as a ':'
    """
    others = {
        "`": "~",
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")",
        "-": "_",
        "=": "+",
        "[": "{",
        "]": "}",
        "\\": "|",
        ";": ":",
        "'": '"',
        ",": "<",
        ".": ">",
        "/": "?",
    }
    if char in ascii_letters:
        return char.upper()
    else:
        # try to get char from hardcoded list, otherwise just return char unchanged
        return others.get(char, char)


def get_typed_strings_f(events, allow_backspace=True):
    """
    Non-generator version of keyboard.get_typed_strings(), with a better
    letter-case calculation.

    See https://github.com/boppreh/keyboard for reference and license.
    """
    backspace_name = (
        "delete" if keyboard._platform.system() == "Darwin" else "backspace"
    )

    shift_pressed = False
    capslock_pressed = False
    string = ""
    for event in events:
        name = event.name

        # Space is the only key that we _parse_hotkey to the spelled out name
        # because of legibility. Now we have to undo that.
        if event.name == "space":
            name = " "

        if "shift" in event.name:
            shift_pressed = event.event_type == "down"
        elif event.name == "caps lock" and event.event_type == "down":
            capslock_pressed = not capslock_pressed
        elif (
            allow_backspace
            and event.name == backspace_name
            and event.event_type == "down"
        ):
            string = string[:-1]
        elif event.event_type == "down":
            if len(name) == 1:
                if shift_pressed ^ capslock_pressed:
                    name = shift(name)
                string = string + name
            else:
                pass
                # return string
    return string


class AggregatedEventDevice(object):
    """
    Modified version of AggregatedEventDevice from the `keyboard` module.

    See https://github.com/boppreh/keyboard for reference and license.
    """

    def __init__(self, devices, output=None):
        self.event_queue = Queue()
        self.devices = devices
        self.output = output or self.devices[0]
        self.thread_map = {}

        def start_reading(device):
            try:
                while True:
                    self.event_queue.put(device.read_event())
            except OSError:
                print("Device unplugged, restarting....")
                restart()

        for device in self.devices:
            thread = Thread(target=start_reading, args=[device])
            thread.setDaemon(True)
            self.thread_map[device] = thread

    def read_event(self):
        return self.event_queue.get(block=True)

    def write_event(self, type, code, value):
        self.output.write_event(type, code, value)

    def start(self):
        """
        Start all the listener threads.

        We don't start the threads in __init__, because this way we can remove
        certain devices from the aggregated device before starting it.
        """
        for thread in self.thread_map.values():
            thread.start()

    def remove_device(self, device):
        del self.thread_map[device]


def patch_event_device():
    # monkeypatch keyboard module
    keyboard._nixcommon.AggregatedEventDevice = AggregatedEventDevice
