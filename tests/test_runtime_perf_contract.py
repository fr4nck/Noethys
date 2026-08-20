#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrats statiques du diagnostic de performance Noethys."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuntimePerformanceContractTests(unittest.TestCase):
    def test_perf_hook_is_loaded_in_dev_and_portable(self):
        dev = (ROOT / "scripts" / "run_noethys_dev.py").read_text(encoding="utf-8")
        spec = (ROOT / "packaging" / "noethys.spec").read_text(encoding="utf-8")
        self.assertIn('runtime_perf.py', dev)
        self.assertIn('runtime_perf.py', spec)

    def test_watchdog_is_ignored_only_before_real_mainloop(self):
        source = (ROOT / "packaging" / "runtime_perf.py").read_text(encoding="utf-8")
        self.assertIn('threading.current_thread().name == "NoethysHangWatchdog"', source)
        self.assertIn('not state["mainloop_started"]', source)
        self.assertIn('state["mainloop_started"] = True', source)
        self.assertIn('state["mainloop_started"] = False', source)

    def test_window_ready_and_mysql_timings_are_recorded(self):
        source = (ROOT / "packaging" / "runtime_perf.py").read_text(encoding="utf-8")
        self.assertIn('noethys_perf.log', source)
        self.assertIn('WINDOW_READY elapsed_ms=', source)
        self.assertIn('MYSQL_%s elapsed_ms=', source)
        self.assertIn('_sanitize_sql(query)', source)

    def test_window_identity_does_not_use_business_title(self):
        source = (ROOT / "packaging" / "runtime_perf.py").read_text(encoding="utf-8")
        start = source.index('def _window_key(window):')
        end = source.index('\n\ndef _sanitize_sql', start)
        block = source[start:end]
        self.assertNotIn('GetTitle', block)
        self.assertIn('__class__.__module__', block)


if __name__ == "__main__":
    unittest.main()
