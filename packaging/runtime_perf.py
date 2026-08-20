# -*- coding: utf-8 -*-
"""Mesures locales de performance pour Noethys.

Le but est de distinguer les lenteurs d'interface des allers-retours MySQL,
notamment quand une base réseau est utilisée à travers un WAN. Le journal ne
stocke ni valeurs saisies, ni paramètres SQL, ni titres métier des fenêtres.

Mesures produites dans ``noethys_perf.log`` :
- délai entre une action GUI et la première phase idle où une nouvelle fenêtre
  de premier niveau est visible ;
- temps des connexions MySQL ;
- temps des requêtes MySQL avec littéraux anonymisés.
"""

import datetime
import os
import re
import sys
import threading
import time


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

PERF_PATH = os.path.join(LOG_DIR, "noethys_perf.log")
_SESSION_ID = "%s-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
_WRITE_LOCK = threading.RLock()
_MAX_LOG_BYTES = 10 * 1024 * 1024


def _append(line):
    try:
        with _WRITE_LOCK:
            if os.path.isfile(PERF_PATH) and os.path.getsize(PERF_PATH) > _MAX_LOG_BYTES:
                previous = PERF_PATH + ".1"
                try:
                    if os.path.exists(previous):
                        os.remove(previous)
                    os.replace(PERF_PATH, previous)
                except Exception:
                    pass
            with open(PERF_PATH, "a", encoding="utf-8", errors="replace") as stream:
                stream.write(line)
                if not line.endswith("\n"):
                    stream.write("\n")
                stream.flush()
    except Exception:
        pass


def _stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _window_key(window):
    try:
        module = window.__class__.__module__ or "?"
        name = window.__class__.__name__ or "?"
    except Exception:
        module, name = "?", "?"
    try:
        wx_name = window.GetName() or ""
    except Exception:
        wx_name = ""
    return "%s.%s name=%r" % (module, name, wx_name)


def _sanitize_sql(query):
    """Conserve la forme de la requête sans ses valeurs métier."""
    if isinstance(query, bytes):
        query = query.decode("utf-8", errors="replace")
    text = str(query)
    text = re.sub(r"'(?:''|\\'|[^'])*'", "'? '".rstrip(), text)
    text = re.sub(r'"(?:""|\\"|[^"])*"', '"?"', text)
    text = re.sub(r"\b0x[0-9a-fA-F]+\b", "?", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "?", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 260:
        text = text[:257] + "..."
    return text


def _log_mysql(kind, elapsed, query=None):
    millis = elapsed * 1000.0
    if query is None:
        _append("%s MYSQL_%s elapsed_ms=%.1f" % (_stamp(), kind, millis))
    else:
        _append("%s MYSQL_%s elapsed_ms=%.1f sql=%r" % (_stamp(), kind, millis, _sanitize_sql(query)))


def _wrap_connect(module, attr="connect", label="CONNECT"):
    original = getattr(module, attr, None)
    if original is None or getattr(original, "__noethys_perf__", False):
        return

    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            _log_mysql(label, time.perf_counter() - start)

    wrapped.__noethys_perf__ = True
    setattr(module, attr, wrapped)


def _wrap_cursor_class(cls, method_name, label):
    original = getattr(cls, method_name, None)
    if original is None or getattr(original, "__noethys_perf__", False):
        return

    def wrapped(self, query, *args, **kwargs):
        start = time.perf_counter()
        try:
            return original(self, query, *args, **kwargs)
        finally:
            _log_mysql(label, time.perf_counter() - start, query=query)

    wrapped.__noethys_perf__ = True
    try:
        setattr(cls, method_name, wrapped)
    except Exception as exc:
        _append("%s PERF_PATCH_FAIL target=%s.%s error=%s" % (_stamp(), getattr(cls, "__name__", "?"), method_name, type(exc).__name__))


def _install_mysql_instrumentation():
    try:
        import MySQLdb
        from MySQLdb import cursors as mysql_cursors

        _wrap_connect(MySQLdb, "connect", "CONNECT_MYSQLDB")
        for cls_name in ("BaseCursor", "Cursor", "DictCursor", "SSCursor", "SSDictCursor"):
            cls = getattr(mysql_cursors, cls_name, None)
            if cls is not None:
                _wrap_cursor_class(cls, "execute", "QUERY_MYSQLDB")
                _wrap_cursor_class(cls, "executemany", "MANY_MYSQLDB")
    except Exception as exc:
        _append("%s PERF_MYSQLDB_UNAVAILABLE error=%s" % (_stamp(), type(exc).__name__))

    try:
        import mysql.connector
        _wrap_connect(mysql.connector, "connect", "CONNECT_CONNECTOR")

        classes = []
        try:
            from mysql.connector import cursor as connector_cursor
            for cls_name in ("MySQLCursor", "MySQLCursorBuffered", "MySQLCursorDict", "MySQLCursorBufferedDict"):
                cls = getattr(connector_cursor, cls_name, None)
                if cls is not None:
                    classes.append(cls)
        except Exception:
            pass
        try:
            from mysql.connector import cursor_cext
            for cls_name in ("CMySQLCursor", "CMySQLCursorBuffered", "CMySQLCursorDict", "CMySQLCursorBufferedDict"):
                cls = getattr(cursor_cext, cls_name, None)
                if cls is not None:
                    classes.append(cls)
        except Exception:
            pass
        for cls in classes:
            _wrap_cursor_class(cls, "execute", "QUERY_CONNECTOR")
            _wrap_cursor_class(cls, "executemany", "MANY_CONNECTOR")
    except Exception as exc:
        _append("%s PERF_CONNECTOR_UNAVAILABLE error=%s" % (_stamp(), type(exc).__name__))


def _install_wx_instrumentation():
    try:
        import wx
    except Exception as exc:
        _append("%s PERF_WX_UNAVAILABLE error=%s" % (_stamp(), type(exc).__name__))
        return

    state = {
        "last_action_time": None,
        "last_action": "startup",
        "known_windows": set(),
        "mainloop_start": None,
    }

    def trace_action(event):
        try:
            state["last_action_time"] = time.perf_counter()
            event_type = event.GetEventType()
            mapping = {
                wx.wxEVT_MENU: "MENU",
                wx.wxEVT_BUTTON: "BUTTON",
                wx.wxEVT_LEFT_DCLICK: "DOUBLE_CLICK",
                wx.wxEVT_LIST_ITEM_ACTIVATED: "LIST_ACTIVATE",
                wx.wxEVT_TREE_ITEM_ACTIVATED: "TREE_ACTIVATE",
            }
            state["last_action"] = mapping.get(event_type, "EVENT_%s" % event_type)
        except Exception:
            pass
        event.Skip()

    def inspect_idle(event):
        try:
            now = time.perf_counter()
            for window in list(wx.GetTopLevelWindows()):
                try:
                    if not window.IsShown():
                        continue
                except Exception:
                    continue
                identity = id(window)
                if identity in state["known_windows"]:
                    continue
                state["known_windows"].add(identity)

                start = state["last_action_time"]
                action = state["last_action"]
                if start is None:
                    start = state["mainloop_start"]
                    action = "STARTUP"
                if start is None:
                    continue
                elapsed = now - start
                if elapsed < 0.0 or elapsed > 15.0:
                    continue
                _append("%s WINDOW_READY elapsed_ms=%.1f action=%s window=%s" % (
                    _stamp(), elapsed * 1000.0, action, _window_key(window)
                ))
        except Exception:
            pass
        event.Skip()

    original_main_loop = wx.App.MainLoop
    if getattr(original_main_loop, "__noethys_perf__", False):
        return

    def main_loop_with_perf(self, *args, **kwargs):
        state["mainloop_start"] = time.perf_counter()
        state["known_windows"] = set()
        try:
            for binder in (
                wx.EVT_MENU,
                wx.EVT_BUTTON,
                wx.EVT_LEFT_DCLICK,
                wx.EVT_LIST_ITEM_ACTIVATED,
                wx.EVT_TREE_ITEM_ACTIVATED,
            ):
                self.Bind(binder, trace_action)
            self.Bind(wx.EVT_IDLE, inspect_idle)
        except Exception as exc:
            _append("%s PERF_WX_BIND_FAIL error=%s" % (_stamp(), type(exc).__name__))
        return original_main_loop(self, *args, **kwargs)

    main_loop_with_perf.__noethys_perf__ = True
    wx.App.MainLoop = main_loop_with_perf


_append("\n===== Noethys performance session %s =====" % _SESSION_ID)
_append("%s PERF_START python=%s platform=%s" % (_stamp(), sys.version.split()[0], sys.platform))
_install_mysql_instrumentation()
_install_wx_instrumentation()
