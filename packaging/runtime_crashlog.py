# -*- coding: utf-8 -*-
"""PyInstaller runtime hook: persist GUI/runtime exceptions for frozen builds.

Noethys is packaged with ``console=False``.  Without an explicit stderr sink,
exceptions raised by wx event handlers can therefore be invisible to the user
and absent from ``journal.log``.  This hook is intentionally independent from
Noethys configuration so it is available from the first instruction executed
by the frozen application.
"""

import datetime
import os
import sys
import traceback


def _user_log_directory():
    """Return the historical portable/user configuration directory."""
    executable_dir = os.path.dirname(os.path.abspath(sys.executable))
    portable_dir = os.path.join(executable_dir, "Portable")
    if os.path.isdir(portable_dir):
        return portable_dir

    roaming = os.environ.get("APPDATA")
    if roaming:
        return os.path.join(roaming, "noethys")
    return executable_dir


LOG_DIR = _user_log_directory()
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    # Last-resort location: next to the executable.
    LOG_DIR = os.path.dirname(os.path.abspath(sys.executable))

JOURNAL_PATH = os.path.join(LOG_DIR, "journal.log")
CRASH_PATH = os.path.join(LOG_DIR, "noethys_crash.log")


class _StderrLog(object):
    """Mirror stderr to journal.log while preserving any existing sink."""

    def __init__(self, previous):
        self.previous = previous
        self.filename = open(JOURNAL_PATH, "a", encoding="utf-8", errors="replace")

    def write(self, text):
        if not text:
            return
        try:
            self.filename.write(text)
            self.filename.flush()
        except Exception:
            pass
        if self.previous is not None:
            try:
                self.previous.write(text)
                self.previous.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self.filename.flush()
        except Exception:
            pass
        if self.previous is not None:
            try:
                self.previous.flush()
            except Exception:
                pass


try:
    sys.stderr = _StderrLog(sys.stderr)
except Exception:
    pass

_previous_excepthook = sys.excepthook


def _format_exception(exctype, value, tb):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n===== Noethys crash %s =====\n%s" % (
        timestamp,
        "".join(traceback.format_exception(exctype, value, tb)),
    )


def _write_crash(exctype, value, tb):
    text = _format_exception(exctype, value, tb)
    try:
        with open(CRASH_PATH, "a", encoding="utf-8", errors="replace") as stream:
            stream.write(text)
            stream.flush()
    except Exception:
        pass
    try:
        sys.stderr.write(text)
    except Exception:
        pass


def _excepthook(exctype, value, tb):
    _write_crash(exctype, value, tb)
    # Preserve Python's normal exception handling semantics where possible.
    try:
        if _previous_excepthook not in (None, _excepthook):
            _previous_excepthook(exctype, value, tb)
    except Exception:
        pass


sys.excepthook = _excepthook

# wx dispatches most GUI callbacks inside MainLoop.  Route those exceptions
# through the same global hook so a dead double-click never becomes silent.
try:
    import wx

    def _on_exception_in_main_loop(self):
        exctype, value, tb = sys.exc_info()
        if exctype is not None:
            sys.excepthook(exctype, value, tb)
        return True

    wx.App.OnExceptionInMainLoop = _on_exception_in_main_loop
except Exception:
    pass
