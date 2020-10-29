#!/usr/bin/env python3

# Imports {{{
# builtins
import ctypes
import fcntl
import json
from json.decoder import JSONDecodeError
import logging
from os import PathLike, geteuid
import threading
import sys
from shutil import get_terminal_size
from typing import Callable, Mapping, NoReturn, Union

# 3rd party
import evdev
from frozendict import frozendict
import ioctl_opt
import keyboard

# local modules
from pi_scan.patches import get_typed_strings_f, patch_event_device

# }}}


log = logging.getLogger(__name__)


class EventAccumulator(object):
    def __init__(self, callback, separators=["enter", "tab"]):
        self.callback = callback
        self.separators = separators
        self.record = {}  # keys = device, values = array of events

    def accumulate(self, event):
        # get events record for the device
        events = self.record.get(event.device, None)
        if events is None:
            self.record[event.device] = []
            events = self.record[event.device]

        # if a separator, collapse the events and call the callback
        if event.name in self.separators and event.event_type == "up":
            string = get_typed_strings_f(events)
            if string:
                self.start_callback(string)
            self.record[event.device] = []
        else:
            events.append(event)

    def start_callback(self, string):
        """
        We pass the queue of events we recorded to a threaded process.
        This parallelizes the API requests to ensure that the program doesn't
        stop reading scans while it waits for a response from the server.
        This way, you can send requests as fast as the scanner can scan them
        """
        t = threading.Thread(
            target=self.callback,
            args=[string],
            daemon=True,
        )
        t.start()


def grab(device_file):
    def EVIOCGRAB():
        return ioctl_opt.IOW(ord("E"), 0x90, ctypes.c_int)

    # grab the device for exclusive use
    fcntl.ioctl(device_file, EVIOCGRAB(), True)


def root():
    return geteuid() == 0


class Listener(object):
    def __init__(
        self,
        callback: Callable,
        config: Union[Mapping, PathLike] = {"name": "Pi-Scan"},
    ):
        self.callback = callback
        if isinstance(config, Mapping):
            self._config = config
        else:
            self._config = {}
            try:
                self._config = config
                json.load(open(config))  # see if it's valid
                log.info(f"Found a valid config file at {str(config)}")
            except FileNotFoundError:
                log.warning(f"No config found at {str(config)}.")
            except JSONDecodeError:
                log.error(f"Config at {str(config)} is not a valid JSON file.")

    @property
    def config(self) -> Mapping:
        if isinstance(self._config, Mapping):
            data = self._config
        else:
            data = json.load(open(self._config))
        return frozendict(data)

    def listen(self) -> NoReturn:
        if not root():
            print(f"You must be root to use Listener.listen()!")
            sys.exit(1)
        print(f"{self.config['name']} started.\n")

        if self.config:
            print(f"Running with:")
            for key, value in self.config.items():
                print(f"  {key.capitalize()}: {value}")
            print()

        patch_event_device()
        keyboard._os_keyboard.init()
        compatible_scanners = [
            (0x2DD6, 0x2A61),
            (0x05E0, 0x1200),
        ]

        # iterate device file pointers in use by keyboard module
        devs = []
        for kbd_dev in keyboard._os_keyboard.device.devices:
            ev_dev = evdev.InputDevice(kbd_dev.input_file.name)
            vendor = ev_dev.info.vendor
            product = ev_dev.info.product

            if (vendor, product) in compatible_scanners:
                devs.append(ev_dev)

                # grab the device for exclusive use
                grab(kbd_dev.input_file)
            else:
                log.info(f"Ignoring '{ev_dev.name}'.")
                keyboard._os_keyboard.device.remove_device(kbd_dev)

        self.report_devs(devs)

        accumulator = EventAccumulator(callback=self.callback)
        if self.config.get("separators") is not None:
            accumulator.separators = self.config["separators"]

        keyboard._os_keyboard.device.start()
        keyboard.hook(accumulator.accumulate)
        keyboard.wait()

    def report_devs(self, devs):
        if not devs:
            log.error("No scanners found. Exiting...")
            sys.exit(1)
        else:
            for dev in devs:
                addr = f"{dev.info.vendor:x}:{dev.info.product:x}"
                print(f"\nFound {dev.name} ({addr}), grabbing for exclusive use...")

        print(f"Scanner{'s' if len(devs) > 1 else ''} initialized. Listening....")
        print(f"{'=' * get_terminal_size().columns}\n")
