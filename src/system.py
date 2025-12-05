"""
Simple interactive command-line component.

Implements 'help' and a functional 'capture' command.
Other commands remain print-only stubs for now.

Tip: use Ctrl-C or Ctrl-D to exit the interactive session.
"""

import os
import time
from datetime import datetime
from typing import Optional, Tuple

import cv2


def print_help() -> None:
    """Print help for available commands (currently only 'help')."""
    lines = [
        "Available commands:",
        "  help        Show this help message",
        "  test        Run system tests (camera, buttons, etc.)",
        "              - -camera (test camera functionality)",
        "              - -button (test button inputs)",
        "              - -model (test ML model loading and inference)",
        "  capture     Capture a single frame from the camera and save it",
        "  reconstruct Run reconstruction on the latest captured frame",
        "  run         Capture and reconstruct in one step",
        "  reset       Reset the system (clear captures and results)",
        "",
        "Exit:",
        "  Press Ctrl-C (KeyboardInterrupt)",
        "  Or Ctrl-D/EOF (EOFError)",
    ]
    print("\n".join(lines))


def start_interactive_cli(prompt: str = "> ", intro: Optional[str] = None) -> None:
    """Start an interactive CLI that currently implements only 'help'.

    Parameters:
        prompt: Prompt text shown to the user.
        intro: Optional additional message printed when the session starts.
    """
    banner = "[CLI] Interactive mode started. Type 'help' to see commands, Ctrl-C to exit."
    if intro:
        print(intro)
    print(banner)

    while True:
        try:
            raw = input(prompt)
        except KeyboardInterrupt:
            print("\n[CLI] Exited (KeyboardInterrupt)")
            break
        except EOFError:
            print("\n[CLI] Exited (EOF)")
            break

        cmd = (raw or "").strip()
        if not cmd:
            continue

        low = cmd.lower()
        if low in ("help", "?", "h"):
            print_help()
            continue

        # test commands (no real implementation; only print)
        if low.startswith("test"):
            parts = low.split()
            target = parts[1] if len(parts) > 1 else None
            if target == "-camera":
                print("[TEST] camera -> running check (prints results)")
                try:
                    from src.camera import check_camera
                    res = check_camera()
                    print(f"[TEST] camera result: {res}")
                except Exception as e:
                    print(f"[TEST] camera error: {e}")
                if target is None:
                    print("[TEST] usage: test camera | test button | test model")
            elif target == "-button":
                print("[TEST] button -> simulate button test (prints only)")
            elif target == "-model":
                print("[TEST] model -> running model asset check (prints results)")
                try:
                    from src.model import check_model
                    res = check_model()
                    print(f"[TEST] model result: {res}")
                except Exception as e:
                    print(f"[TEST] model error: {e}")
            else:
                print(f"[TEST] unknown target: {target}")
            continue

        if low in ("capture", "c"):
            try:
                from src.camera import capture_once
                path = capture_once()
                print(f"[CAPTURE] saved -> {path}")
            except Exception as e:
                print(f"[CAPTURE] error: {e}")
            continue

        if low in ("reconstruct", "r"):
            try:
                from src.model import reconstruct_latest
                out_png = reconstruct_latest()
                print(f"[RECONSTRUCT] plot saved -> {out_png}")
            except Exception as e:
                print(f"[RECONSTRUCT] error: {e}")
            continue

        if low == "run":
            try:
                from src.camera import capture_once
                from src.model import reconstruct_latest
                path = capture_once()
                print(f"[RUN] capture saved -> {path}")
                out_png = reconstruct_latest()
                print(f"[RUN] reconstruct saved -> {out_png}")
            except Exception as e:
                print(f"[RUN] error: {e}")
            continue

        if low == "reset":
            try:
                reset_workspace()
            except Exception as e:
                print(f"[RESET] error: {e}")
            continue

        # Unrecognized commands show help prompt
        print(f"Unknown command: {cmd}. Type 'help' for assistance.")


def start_system() -> None:
    """Start system in CLI or button mode based on environment or input.

    Selection precedence:
    1) Environment variable MODE: "buttons" or "cli".
    2) Command-line prompt at start: type "buttons" to enter button mode; otherwise CLI.
    """
    mode_env = os.environ.get("MODE", "").strip().lower()
    if mode_env == "buttons":
        try:
            from src.button import start_control_buttons
            print("[SYSTEM] Starting in buttons mode (env MODE)")
            start_control_buttons()
            return
        except Exception as e:
            print(f"[SYSTEM] buttons mode error: {e}. Falling back to CLI.")

    # Prompt user once for mode selection
    try:
        choice = input("Select mode [cli/buttons]: ").strip().lower()
    except Exception:
        choice = "cli"

    if choice == "buttons":
        try:
            from src.button import start_control_buttons
            print("[SYSTEM] Starting in buttons mode")
            start_control_buttons()
            return
        except Exception as e:
            print(f"[SYSTEM] buttons mode error: {e}. Falling back to CLI.")

    # Default to CLI
    start_interactive_cli()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CAPTURE_DIR = os.path.join(PROJECT_ROOT, "capture")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")


def _safe_rm(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except Exception:
        return False


def _list_files(folder: str) -> list[str]:
    try:
        import glob
        return sorted(glob.glob(os.path.join(folder, "*")))
    except Exception:
        return []


def reset_workspace() -> None:
    """Remove files under capture/ and result/ folders."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    c_files = _list_files(CAPTURE_DIR)
    r_files = _list_files(RESULT_DIR)
    c_ok = sum(_safe_rm(p) for p in c_files)
    r_ok = sum(_safe_rm(p) for p in r_files)
    print(f"[RESET] removed {c_ok} capture files, {r_ok} result files")


__all__ = ["start_interactive_cli", "print_help", "start_system", "reset_workspace"]