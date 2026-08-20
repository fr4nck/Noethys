# -*- coding: utf-8 -*-
"""Diagnostics runtime précoces pour les builds PyInstaller de Noethys.

Le portable Windows est construit avec ``console=False`` : une exception wx,
un thread en erreur ou un gel de la boucle GUI peut donc être invisible. Ce
hook reste indépendant de la configuration et de la base Noethys afin d'être
actif avant le premier import métier.

Fichiers produits :
- ``journal.log`` : stderr + en-tête technique de session ;
- ``noethys_crash.log`` : exceptions Python, wx, threads, unraisable et erreurs
  fatales prises en charge par faulthandler ;
- ``noethys_hang.log`` : état de tous les threads si la boucle wx ne répond plus
  pendant environ 30 secondes.

Aucune configuration utilisateur, aucun mot de passe et aucun contenu métier
n'est collecté par ce hook.
"""

import datetime
import faulthandler
import os
import sys
import threading
import time
import traceback


def _user_log_directory():
    """Retourne le dossier historique portable/configuration utilisateur."""
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

_SESSION_ID = "%s-%s" % (
    datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
    os.getpid(),
)
_WRITE_LOCK = threading.RLock()
_WX = None


def _append(path, text):
    try:
        with _WRITE_LOCK:
            with open(path, "a", encoding="utf-8", errors="replace") as stream:
                stream.write(text)
                stream.flush()
    except Exception:
        pass


def _read_build_info():
    """Lit uniquement BUILD-INFO.txt, généré par notre workflow de packaging."""
    path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "BUILD-INFO.txt")
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as stream:
            lines = [line.strip() for line in stream if line.strip()]
        return " | ".join(lines[:12])
    except Exception:
        return "BUILD-INFO.txt absent"


def _window_context():
    """Retourne uniquement les métadonnées de fenêtres, jamais leur contenu."""
    if _WX is None:
        return "wx: non chargé"
    try:
        active = _WX.GetActiveWindow()
        if active is None:
            active_text = "none"
        else:
            try:
                title = active.GetTitle()
            except Exception:
                title = ""
            active_text = "%s title=%r" % (active.__class__.__name__, title)

        windows = []
        for window in list(_WX.GetTopLevelWindows())[:12]:
            try:
                title = window.GetTitle()
            except Exception:
                title = ""
            try:
                shown = window.IsShown()
            except Exception:
                shown = "?"
            try:
                enabled = window.IsEnabled()
            except Exception:
                enabled = "?"
            windows.append(
                "%s(title=%r, shown=%s, enabled=%s)"
                % (window.__class__.__name__, title, shown, enabled)
            )
        return "active=%s | top=%s" % (active_text, "; ".join(windows) or "none")
    except Exception as exc:
        return "wx context unavailable: %s: %s" % (type(exc).__name__, exc)


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
    return "\n".join(lines)


class _StderrLog(object):
    """Recopie stderr vers journal.log tout en conservant l'ancien flux."""

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


# En-tête léger à chaque exécution : il permet d'identifier immédiatement le
# commit/build réellement testé sans attendre une exception.
_append(
    JOURNAL_PATH,
    "\n===== Noethys diagnostics session start =====\n%s\n" % _technical_context("session-start"),
)


# faulthandler couvre les erreurs natives que sys.excepthook ne voit pas. Le
# handle doit rester ouvert pendant toute la vie du processus.
_FAULT_STREAM = None
try:
    _FAULT_STREAM = open(CRASH_PATH, "a", encoding="utf-8", errors="replace")
    _FAULT_STREAM.write(
        "\n===== faulthandler armed session %s =====\n%s\n"
        % (_SESSION_ID, _technical_context("faulthandler-armed"))
    )
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
    text = (
        "\n===== Noethys crash =====\n%s\n--- traceback ---\n%s"
        % (context, trace)
    )
    _append(CRASH_PATH, text)
    _dump_all_threads(CRASH_PATH, "crash")
    try:
        sys.stderr.write(text)
    except Exception:
        pass


def _excepthook(exctype, value, tb):
    _write_crash(exctype, value, tb, kind="sys.excepthook")
    # N'appelle un hook précédent que s'il était réellement personnalisé. Le
    # hook Python par défaut recopierait simplement la traceback une deuxième fois.
    try:
        if _previous_excepthook not in (None, sys.__excepthook__, _excepthook):
            _previous_excepthook(exctype, value, tb)
    except Exception:
        pass


sys.excepthook = _excepthook


# Python 3.8+ : une exception d'un worker n'arrive pas dans sys.excepthook.
_previous_thread_excepthook = getattr(threading, "excepthook", None)
if _previous_thread_excepthook is not None:
    def _thread_excepthook(args):
        thread = getattr(args, "thread", None)
        extra = "worker=%s ident=%s" % (
            getattr(thread, "name", "?"),
            getattr(thread, "ident", "?"),
        )
        _write_crash(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            kind="threading.excepthook",
            extra=extra,
        )
        try:
            default = getattr(threading, "__excepthook__", None)
            if _previous_thread_excepthook not in (None, default, _thread_excepthook):
                _previous_thread_excepthook(args)
        except Exception:
            pass

    threading.excepthook = _thread_excepthook


# Erreurs de destructeurs/finalizers et autres exceptions non remontables.
_previous_unraisablehook = getattr(sys, "unraisablehook", None)
if _previous_unraisablehook is not None:
    def _unraisablehook(args):
        obj = getattr(args, "object", None)
        try:
            obj_text = repr(obj)[:300]
        except Exception:
            obj_text = "<repr unavailable>"
        _write_crash(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            kind="sys.unraisablehook",
            extra="object=%s" % obj_text,
        )
        try:
            default = getattr(sys, "__unraisablehook__", None)
            if _previous_unraisablehook not in (None, default, _unraisablehook):
                _previous_unraisablehook(args)
        except Exception:
            pass

    sys.unraisablehook = _unraisablehook


# Watchdog de gel GUI. Il ne ferme jamais l'application : il écrit seulement
# les stacks lorsqu'aucun heartbeat wx n'a été traité pendant 30 secondes.
_GUI_TIMEOUT_SECONDS = 30.0
_WATCHDOG_POLL_SECONDS = 5.0
_HEARTBEAT_INTERVAL_MS = 2000
_last_gui_heartbeat = time.monotonic()
_hang_reported = False
_heartbeat_calllater = None


def _write_hang(delay):
    text = (
        "\n===== Noethys GUI hang detected =====\n%s\n"
        % _technical_context(
            "gui-hang",
            extra="heartbeat stale for %.1f seconds" % delay,
        )
    )
    _append(HANG_PATH, text)
    _append(JOURNAL_PATH, "\n[DIAGNOSTIC] Gel GUI détecté (%.1f s). Voir noethys_hang.log\n" % delay)
    _dump_all_threads(HANG_PATH, "GUI hang")


def _watchdog_loop():
    global _hang_reported, _last_gui_heartbeat
    while True:
        time.sleep(_WATCHDOG_POLL_SECONDS)
        try:
            if _WX is None or _WX.GetApp() is None:
                # Avant la création de wx.App, aucun heartbeat n'est attendu.
                _last_gui_heartbeat = time.monotonic()
                continue
            delay = time.monotonic() - _last_gui_heartbeat
            if delay >= _GUI_TIMEOUT_SECONDS and not _hang_reported:
                _hang_reported = True
                _write_hang(delay)
        except Exception:
            pass


try:
    import wx

    _WX = wx

    # Enrichit l'en-tête avec la version wx dès qu'elle est disponible.
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
            wx.CallAfter(_gui_heartbeat)
        except Exception:
            pass
        return _original_main_loop(self, *args, **kwargs)

    wx.App.MainLoop = _main_loop_with_watchdog

    threading.Thread(
        target=_watchdog_loop,
        name="NoethysHangWatchdog",
        daemon=True,
    ).start()
except Exception as exc:
    _append(
        JOURNAL_PATH,
        "[DIAGNOSTIC] Initialisation wx du crash logger impossible: %s: %s\n"
        % (type(exc).__name__, exc),
    )
