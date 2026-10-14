"""
The state hue keeps for the length of one request.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from hue.shortcuts import shortcuts
from hue.toast import toast


@contextmanager
def request_scope() -> Iterator[bool]:
    """
    Open the toast queue and the list of scoped shortcuts for as long as the
    block runs, and close them however it ends.

    The router opens it around every handler, and HueRequestMiddleware around
    a whole Django request, so that a plain view has it too. Whichever opens
    first owns it: the other finds it open and leaves it to them. The block
    is told whether it owns the toast queue, since a toast that nothing outside
    will carry on is the owner's to report.
    """
    toast_token = toast.open()
    shortcuts_token = shortcuts.open()
    try:
        yield toast_token is not None
    finally:
        toast.close(toast_token)
        shortcuts.close(shortcuts_token)
