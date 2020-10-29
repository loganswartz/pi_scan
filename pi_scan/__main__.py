#!/usr/bin/env python3

# Imports {{{
# builtins

# 3rd party modules

# local modules
from pi_scan.listen import Listener

# }}}


def echo_scan(scanned: str):
    print(f"Scanned --> {repr(scanned)}")


try:
    listener = Listener(echo_scan)
    listener.listen()
except KeyboardInterrupt:
    print("Exiting....")
