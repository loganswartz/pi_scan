#!/usr/bin/env python3

# Imports {{{
# builtins
import os
import sys
import ctypes

# }}}


def root():
    return os.geteuid() == 0


def restart():
    """
    Restart the entire Python process.

    This completely restarts the process with all the same arguments and
    environment variables of the current process.

    Second argument of exec() is given extra quotes in case it's called on
    Windows and has a space in the name.
    """

    def get_interpreter_call_signature():

        argc = ctypes.c_int()
        argv = ctypes.POINTER(
            ctypes.c_wchar_p if sys.version_info >= (3,) else ctypes.c_char_p
        )()
        ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(argc), ctypes.byref(argv))

        # Ctypes are weird. They can't be used in list comprehensions, you can't use `in` with them, and you can't
        # use a for-each loop on them. We have to do an old-school for-i loop.
        arguments = list()
        for i in range(argc.value - len(sys.argv) + 1):
            arguments.append(argv[i])

        return arguments

    os.execl(sys.executable, *get_interpreter_call_signature(), *sys.argv[1:])
