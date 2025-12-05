"""
Button layer: gpiozero-based four-button mapping (reset/run/capture/reconstruct).

Provides:
- start_control_buttons(pins=None): bind four buttons to reset/run/capture/reconstruct.
"""

from typing import List, Callable


def start_control_buttons(pins: List[int] | None = None) -> None:
	"""Bind four buttons to reset, run, capture, reconstruct.

	Default BCM pins: [17, 18, 27, 22]
	Mapping order: reset, run, capture, reconstruct
	"""
	try:
		from gpiozero import Button
	except Exception:
		print("[BUTTON] gpiozero not available. Install on Raspberry Pi.")
		return

	# Lazy imports to avoid heavy deps when not used
	from src.system import reset_captures
	from src.camera import capture_once
	from src.model import reconstruct_latest

	pins = pins or [17, 18, 27, 22]
	actions: List[Callable[[], None]] = [
		lambda: (print("[BUTTON] reset"), reset_captures()),
		lambda: (print("[BUTTON] run"), _do_run(capture_once, reconstruct_latest)),
		lambda: (print("[BUTTON] capture"), _safe_call(capture_once)),
		lambda: (print("[BUTTON] reconstruct"), _safe_call(reconstruct_latest)),
	]

	btns = [Button(p, pull_up=True, bounce_time=0.05, hold_time=1.0) for p in pins]
	for b, fn in zip(btns, actions):
		b.when_pressed = fn

	print("[BUTTON] Control mode on pins:", pins)
	print("[BUTTON] Mapping: reset, run, capture, reconstruct")
	print("[BUTTON] Press Ctrl-C to exit.")
	try:
		while True:
			import time
			time.sleep(1.0)
	except KeyboardInterrupt:
		print("\n[BUTTON] Exit")


def _safe_call(fn: Callable[[], object]) -> None:
	try:
		res = fn()
		if res is not None:
			print(f"[BUTTON] done -> {res}")
	except Exception as e:
		print(f"[BUTTON] error: {e}")


def _do_run(capture_fn: Callable[[], str], reconstruct_fn: Callable[[], str]) -> None:
	try:
		path = capture_fn()
		print(f"[RUN] capture saved -> {path}")
		out_png = reconstruct_fn()
		print(f"[RUN] reconstruct saved -> {out_png}")
	except Exception as e:
		print(f"[RUN] error: {e}")


__all__ = ["start_control_buttons"]
