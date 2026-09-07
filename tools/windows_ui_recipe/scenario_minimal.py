from __future__ import annotations

import argparse
import sys
from pathlib import Path

from noethys_ui_driver import NoethysUiDriver, ScenarioRecorder, StepStatus

SCENARIO = "noethys-vanilla-minimal-close-reopen"
WAITING_TITLE = "Liste d'attente"
CONSUMPTION_TITLE = "Liste détaillée des consommations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive Windows recipe prototype for Noethys Vanilla")
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--profile-root", required=True, type=Path)
    parser.add_argument("--expected-db-host", required=True)
    parser.add_argument("--expected-db-name", required=True)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/noethys-ui"))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--consumption-menu-item", default="Liste détaillée des consommations")
    return parser.parse_args()


def failed(result) -> bool:
    return result.status != StepStatus.PASS.value


def exit_code(status: str) -> int:
    return {"PASS": 0, "FAIL": 10, "TIMEOUT": 11, "CRASH": 12}.get(status, 13)


def wait_main_and_probe(driver: NoethysUiDriver) -> str:
    main = driver.wait_main_window()
    dumps = driver.dump_window_accessibility(int(main.handle), "step-2-main-window")
    return f"main={driver._text(main)!r}; accessibility_dumps={dumps}"


def open_and_wait(driver: NoethysUiDriver, item: str, title: str, probe: str | None = None) -> str:
    driver.choose_menu_item("Consommations", item)
    dialog = driver.wait_dialog(title)
    driver.wait_responsive(int(dialog.handle), timeout=min(driver.default_timeout, 10.0))
    dumps = driver.dump_window_accessibility(int(dialog.handle), probe) if probe else []
    return f"dialog={title!r} visible hwnd={dialog.handle}; accessibility_dumps={dumps}"


def close_button_and_check(driver: NoethysUiDriver, title: str) -> str:
    driver.close_dialog_button(title, "Fermer")
    driver.wait_responsive(driver.main_hwnd, timeout=min(driver.default_timeout, 10.0))
    return f"dialog={title!r} closed via Fermer; Noethys alive"


def trigger_consumption_open(driver: NoethysUiDriver, item: str) -> str:
    driver.choose_menu_item("Consommations", item)
    driver.ensure_alive()
    return "menu click injected; no internal Noethys handler called directly"


def close_first_visible(driver: NoethysUiDriver, title: str) -> str:
    # DLG_Liste_consommations builds and loads its list synchronously before
    # ShowModal(). A real user cannot close the hidden construction phase.
    dialog = driver.wait_dialog(title, visible_only=True)
    driver.close_dialog_button(title, "Fermer")
    driver.wait_responsive(driver.main_hwnd, timeout=min(driver.default_timeout, 10.0))
    return f"first user-visible hwnd={dialog.handle} closed immediately via Fermer"


def repeat_close_reopen(driver: NoethysUiDriver, item: str, title: str, count: int) -> str:
    for _index in range(1, count + 1):
        driver.close_dialog_button(title, "Fermer")
        driver.choose_menu_item("Consommations", item)
        dialog = driver.wait_dialog(title)
        driver.wait_responsive(int(dialog.handle), timeout=min(driver.default_timeout, 10.0))
        driver.ensure_alive()
    return f"{count}/{count} close/reopen cycles completed; last dialog remains open for X test"


def close_x_and_check(driver: NoethysUiDriver, title: str) -> str:
    driver.close_dialog_x(title)
    driver.wait_responsive(driver.main_hwnd, timeout=min(driver.default_timeout, 10.0))
    return f"dialog={title!r} closed by the real Windows title-bar X"


def final_check(driver: NoethysUiDriver) -> str:
    driver.ensure_alive()
    driver.wait_responsive(driver.main_hwnd, timeout=min(driver.default_timeout, 10.0))
    state = driver.process_state()
    if state.get("hung") or state.get("responsive") is False:
        raise RuntimeError(f"Noethys alive but non-responsive: {state}")
    return f"Noethys.exe alive and responsive: {state}"


def main() -> int:
    args = parse_args()
    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")
    artifacts = args.artifacts.resolve()
    driver = NoethysUiDriver(
        args.exe,
        args.profile_root,
        args.expected_db_host,
        args.expected_db_name,
        artifacts,
        default_timeout=args.timeout,
    )
    rec = ScenarioRecorder(driver, SCENARIO, artifacts / "scenario.jsonl")

    steps = [
        ("1", "Launch Noethys.exe with isolated recipe profile", "Process starts and remains alive", lambda: f"pid={driver.launch()}"),
        ("2", "Wait for main window", "Main Noethys window visible and responsive", lambda: wait_main_and_probe(driver)),
        ("3", "Open Affichage menu", "Affichage menu popup visible", lambda: (driver.open_menu("Affichage") and "Affichage opened by click_input")),
        ("4", "Dismiss Affichage with Escape", "Menu closes and process stays alive", lambda: (driver.dismiss_menu() or "Affichage dismissed with ESC")),
        ("5", "Open Consommations > Liste d'attente", "Liste d'attente dialog visible", lambda: open_and_wait(driver, "Liste d'attente", WAITING_TITLE, "step-5-waiting-list")),
        ("6", "Close Liste d'attente using Fermer", "Dialog closes and Noethys stays responsive", lambda: close_button_and_check(driver, WAITING_TITLE)),
        ("7", f"Trigger Consommations > {args.consumption_menu_item}", "Consumption-list open action injected by real menu click", lambda: trigger_consumption_open(driver, args.consumption_menu_item)),
        ("8", "Close consumption dialog at first user-visible opportunity", "Dialog closes without exit or hang", lambda: close_first_visible(driver, CONSUMPTION_TITLE)),
        ("9", "Reopen consumption dialog immediately", "Dialog reopens and is responsive", lambda: open_and_wait(driver, args.consumption_menu_item, CONSUMPTION_TITLE, "step-9-consumption-list")),
        ("10", f"Repeat close/reopen {args.repeat} times", "Every cycle succeeds while process remains responsive", lambda: repeat_close_reopen(driver, args.consumption_menu_item, CONSUMPTION_TITLE, args.repeat)),
        ("11", "Close consumption dialog using Windows X", "Real title-bar close button closes dialog", lambda: close_x_and_check(driver, CONSUMPTION_TITLE)),
        ("12", "Verify Noethys after stress", "Noethys.exe alive and responsive", lambda: final_check(driver)),
    ]

    last = None
    for step, action, expected, operation in steps:
        last = rec.run_step(step, action, expected, operation)
        if failed(last):
            return exit_code(last.status)
    return exit_code(last.status if last else "FAIL")


if __name__ == "__main__":
    sys.exit(main())
