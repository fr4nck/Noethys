# -*- coding: utf-8 -*-
"""Diagnostics runtime précoces pour les builds PyInstaller de Noethys.

Le portable Windows est construit avec ``console=False`` : une exception wx,
un thread en erreur ou un gel de la boucle GUI peut donc être invisible. Ce
hook reste indépendant de la configuration et de la base Noethys afin d'être
actif avant le premier import métier.

Fichiers produits :
- ``journal.log`` : stderr + en-tête technique de session ;
- ``noethys_actions.log`` : chronologie des actions GUI (clics, menus,
  double-clics, onglets, fenêtres) sans contenu métier ;
- ``noethys_crash.log`` : exceptions Python, wx, threads, unraisable et erreurs
  fatales prises en charge par faulthandler ;
- ``noethys_hang.log`` : état de tous les threads si la boucle wx ne répond plus
  pendant environ 30 secondes.

Aucune configuration utilisateur, aucun mot de passe, aucun texte saisi et
aucun contenu métier n'est collecté par ce hook.
"""

import datetime
import faulthandler
import os
import sys
import threading
import time
import traceback


def _user_log_directory():
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
    LOG_DIR = os.path.dirname(os.path.abspath(sys.executable))

JOURNAL_PATH = os.path.join(LOG_DIR, "journal.log")
CRASH_PATH = os.path.join(LOG_DIR, "noethys_crash.log")
HANG_PATH = os.path.join(LOG_DIR, "noethys_hang.log")
ACTION_PATH = os.path.join(LOG_DIR, "noethys_actions.log")

_SESSION_ID = "%s-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
_WRITE_LOCK = threading.RLock()
_WX = None
_ACTION_SEQ = 0
_ACTION_RING = []
_ACTION_RING_MAX = 80


def _append(path, text):
    try:
        with _WRITE_LOCK:
            with open(path, "a", encoding="utf-8", errors="replace") as stream:
                stream.write(text)
                stream.flush()
    except Exception:
        pass


def _read_build_info():
    path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "BUILD-INFO.txt")
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as stream:
            lines = [line.strip() for line in stream if line.strip()]
        return " | ".join(lines[:12])
    except Exception:
        return "BUILD-INFO.txt absent"


def _safe_window(window):
    if window is None:
        return "none"
    parts = [window.__class__.__name__]
    try:
        name = window.GetName()
        if name:
            parts.append("name=%r" % name)
    except Exception:
        pass
    try:
        if hasattr(window, "GetTitle"):
            title = window.GetTitle()
            if title:
                parts.append("title=%r" % title)
    except Exception:
        pass
    try:
        wid = window.GetId()
        parts.append("id=%s" % wid)
    except Exception:
        pass
    return " ".join(parts)


def _window_context():
    if _WX is None:
        return "wx: non chargé"
    try:
        active = _WX.GetActiveWindow()
        windows = []
        for window in list(_WX.GetTopLevelWindows())[:16]:
            try:
                shown = window.IsShown()
            except Exception:
                shown = "?"
            try:
                enabled = window.IsEnabled()
            except Exception:
                enabled = "?"
            windows.append("%s shown=%s enabled=%s" % (_safe_window(window), shown, enabled))
        return "active=%s | top=%s" % (_safe_window(active), "; ".join(windows) or "none")
    except Exception as exc:
        return "wx context unavailable: %s: %s" % (type(exc).__name__, exc)


def _recent_actions_text():
    with _WRITE_LOCK:
        if not _ACTION_RING:
            return "none"
        return "\n".join(_ACTION_RING[-30:])


def _technical_context(kind, extra=None):
    current = threading.current_thread()
    main = threading.main_thread()
    lines = [
        "kind: %s" % kind,
        "session: %s" % _SESSION_ID,
        "time: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pid: %s" % os.getpid(),
        "python: %s" % sys.version.replace("\n", " "),
        "platform: %s / os.name=%s" % (sys.platform, os.name),
        "frozen: %s" % bool(getattr(sys, "frozen", False)),
        "executable: %s" % os.path.abspath(sys.executable),
        "thread: %s ident=%s daemon=%s" % (current.name, current.ident, current.daemon),
        "main-thread: %s ident=%s" % (main.name, main.ident),
        "build: %s" % _read_build_info(),
    ]
    if _WX is not None:
        try:
            lines.append("wx: %s" % _WX.version())
        except Exception:
            pass
        lines.append("windows: %s" % _window_context())
    if extra:
        lines.append("extra: %s" % extra)
    lines.append("recent-actions:\n%s" % _recent_actions_text())
    return "\n".join(lines)


class _StderrLog(object):
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

_append(JOURNAL_PATH, "\n===== Noethys diagnostics session start =====\n%s\n" % _technical_context("session-start"))
_append(ACTION_PATH, "\n===== Noethys action trace session %s =====\n" % _SESSION_ID)

_FAULT_STREAM = None
try:
    _FAULT_STREAM = open(CRASH_PATH, "a", encoding="utf-8", errors="replace")
    _FAULT_STREAM.write("\n===== faulthandler armed session %s =====\n%s\n" % (_SESSION_ID, _technical_context("faulthandler-armed")))
    _FAULT_STREAM.flush()
    faulthandler.enable(file=_FAULT_STREAM, all_threads=True)
except Exception:
    _FAULT_STREAM = None


def _dump_all_threads(path, label):
    try:
        with _WRITE_LOCK:
            with open(path, "a", encoding="utf-8", errors="replace") as stream:
                stream.write("\n--- %s: all Python thread stacks ---\n" % label)
                stream.flush()
                faulthandler.dump_traceback(file=stream, all_threads=True)
                stream.write("--- end thread stacks ---\n")
                stream.flush()
    except Exception:
        pass


_previous_excepthook = sys.excepthook


def _write_crash(exctype, value, tb, kind="uncaught", extra=None):
    context = _technical_context(kind, extra=extra)
    trace = "".join(traceback.format_exception(exctype, value, tb))
    text = "\n===== Noethys crash =====\n%s\n--- traceback ---\n%s" % (context, trace)
    _append(CRASH_PATH, text)
    _dump_all_threads(CRASH_PATH, "crash")
    try:
        sys.stderr.write(text)
    except Exception:
        pass


def _excepthook(exctype, value, tb):
    _write_crash(exctype, value, tb, kind="sys.excepthook")
    try:
        if _previous_excepthook not in (None, sys.__excepthook__, _excepthook):
            _previous_excepthook(exctype, value, tb)
    except Exception:
        pass


sys.excepthook = _excepthook

_previous_thread_excepthook = getattr(threading, "excepthook", None)
if _previous_thread_excepthook is not None:
    def _thread_excepthook(args):
        thread = getattr(args, "thread", None)
        extra = "worker=%s ident=%s" % (getattr(thread, "name", "?"), getattr(thread, "ident", "?"))
        _write_crash(args.exc_type, args.exc_value, args.exc_traceback, kind="threading.excepthook", extra=extra)
        try:
            default = getattr(threading, "__excepthook__", None)
            if _previous_thread_excepthook not in (None, default, _thread_excepthook):
                _previous_thread_excepthook(args)
        except Exception:
            pass
    threading.excepthook = _thread_excepthook

_previous_unraisablehook = getattr(sys, "unraisablehook", None)
if _previous_unraisablehook is not None:
    def _unraisablehook(args):
        obj = getattr(args, "object", None)
        try:
            obj_text = repr(obj)[:300]
        except Exception:
            obj_text = "<repr unavailable>"
        _write_crash(args.exc_type, args.exc_value, args.exc_traceback, kind="sys.unraisablehook", extra="object=%s" % obj_text)
        try:
            default = getattr(sys, "__unraisablehook__", None)
            if _previous_unraisablehook not in (None, default, _unraisablehook):
                _previous_unraisablehook(args)
        except Exception:
            pass
    sys.unraisablehook = _unraisablehook

_GUI_TIMEOUT_SECONDS = 30.0
_WATCHDOG_POLL_SECONDS = 5.0
_HEARTBEAT_INTERVAL_MS = 2000
_last_gui_heartbeat = time.monotonic()
_hang_reported = False
_heartbeat_calllater = None


def _write_hang(delay):
    text = "\n===== Noethys GUI hang detected =====\n%s\n" % _technical_context("gui-hang", extra="heartbeat stale for %.1f seconds" % delay)
    _append(HANG_PATH, text)
    _append(JOURNAL_PATH, "\n[DIAGNOSTIC] Gel GUI détecté (%.1f s). Voir noethys_hang.log\n" % delay)
    _dump_all_threads(HANG_PATH, "GUI hang")


def _watchdog_loop():
    global _hang_reported, _last_gui_heartbeat
    while True:
        time.sleep(_WATCHDOG_POLL_SECONDS)
        try:
            if _WX is None or _WX.GetApp() is None:
                _last_gui_heartbeat = time.monotonic()
                continue
            delay = time.monotonic() - _last_gui_heartbeat
            if delay >= _GUI_TIMEOUT_SECONDS and not _hang_reported:
                _hang_reported = True
                _write_hang(delay)
        except Exception:
            pass


def _event_name(event):
    try:
        et = event.GetEventType()
        mapping = {
            _WX.wxEVT_MENU: "MENU",
            _WX.wxEVT_BUTTON: "BUTTON",
            _WX.wxEVT_LEFT_DCLICK: "DOUBLE_CLICK",
            _WX.wxEVT_LIST_ITEM_ACTIVATED: "LIST_ACTIVATE",
            _WX.wxEVT_NOTEBOOK_PAGE_CHANGED: "NOTEBOOK_PAGE",
            _WX.wxEVT_TREE_ITEM_ACTIVATED: "TREE_ACTIVATE",
            _WX.wxEVT_CLOSE_WINDOW: "CLOSE",
        }
        return mapping.get(et, "EVENT_%s" % et)
    except Exception:
        return "EVENT"


def _menu_label(event):
    try:
        active = _WX.GetActiveWindow()
        if active is None or not hasattr(active, "GetMenuBar"):
            return ""
        bar = active.GetMenuBar()
        if bar is None:
            return ""
        item = bar.FindItemById(event.GetId())
        if item is None:
            return ""
        label = item.GetItemLabelText()
        return label or ""
    except Exception:
        return ""


def _trace_action(event):
    """Trace l'intention GUI sans lire valeurs de champs ni données métier."""
    global _ACTION_SEQ
    try:
        name = _event_name(event)
        obj = event.GetEventObject()
        target = _safe_window(obj)
        label = _menu_label(event) if name == "MENU" else ""
        active = _safe_window(_WX.GetActiveWindow())
        _ACTION_SEQ += 1
        line = "%s #%06d %-15s target=[%s] active=[%s]" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            _ACTION_SEQ,
            name,
            target,
            active,
        )
        if label:
            line += " menu=%r" % label
        line += "\n"
        with _WRITE_LOCK:
            _ACTION_RING.append(line.rstrip())
            if len(_ACTION_RING) > _ACTION_RING_MAX:
                del _ACTION_RING[:-_ACTION_RING_MAX]
        _append(ACTION_PATH, line)
    except Exception:
        pass


try:
    import wx
    _WX = wx
    _append(JOURNAL_PATH, "wx runtime: %s\n" % wx.version())

    def _on_exception_in_main_loop(self):
        exctype, value, tb = sys.exc_info()
        if exctype is not None:
            _write_crash(exctype, value, tb, kind="wx.MainLoop callback")
        return True

    wx.App.OnExceptionInMainLoop = _on_exception_in_main_loop

    def _gui_heartbeat():
        global _last_gui_heartbeat, _hang_reported, _heartbeat_calllater
        _last_gui_heartbeat = time.monotonic()
        _hang_reported = False
        try:
            if wx.GetApp() is not None:
                _heartbeat_calllater = wx.CallLater(_HEARTBEAT_INTERVAL_MS, _gui_heartbeat)
        except Exception:
            pass

    _original_main_loop = wx.App.MainLoop

    def _main_loop_with_watchdog(self, *args, **kwargs):
        global _last_gui_heartbeat
        _last_gui_heartbeat = time.monotonic()
        try:
            # Filtre global : capture les actions structurantes avant leur handler.
            for binder in (
                wx.EVT_MENU,
                wx.EVT_BUTTON,
                wx.EVT_LEFT_DCLICK,
                wx.EVT_LIST_ITEM_ACTIVATED,
                wx.EVT_NOTEBOOK_PAGE_CHANGED,
                wx.EVT_TREE_ITEM_ACTIVATED,
                wx.EVT_CLOSE,
            ):
                self.Bind(binder, _trace_action)
            wx.CallAfter(_gui_heartbeat)
        except Exception as exc:
            _append(JOURNAL_PATH, "[DIAGNOSTIC] Action tracer partiel: %s: %s\n" % (type(exc).__name__, exc))
        return _original_main_loop(self, *args, **kwargs)

    wx.App.MainLoop = _main_loop_with_watchdog

    threading.Thread(target=_watchdog_loop, name="NoethysHangWatchdog", daemon=True).start()
except Exception as exc:
    _append(JOURNAL_PATH, "[DIAGNOSTIC] Initialisation wx du crash logger impossible: %s: %s\n" % (type(exc).__name__, exc))
