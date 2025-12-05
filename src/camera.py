"""
Camera utilities: connectivity checks and capture helpers.

Functions:
- check_camera(device_index=0, out_dir="capture", resolution=(1280, 720), timeout_sec=5.0)
	Verifies camera connectivity: can open, can read a frame, and can save a screenshot.
- capture_once(device_index=0, resolution=(1280, 720), timeout_sec=5.0, out_dir=None, backend=None)
	Captures one frame and saves it into capture/ directory.
"""

import os
import time
from datetime import datetime
from typing import Tuple, Dict, Any

import cv2


def _ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def check_camera(
	device_index: int = 0,
	out_dir: str = "capture",
	resolution: Tuple[int, int] = (1280, 720),
	timeout_sec: float = 5.0,
) -> Dict[str, Any]:
	"""Check camera connectivity and screenshot saving capability.

	Returns dict:
	- opened: whether the device opened successfully
	- captured: whether a frame was captured successfully
	- saved: whether the screenshot was saved successfully
	- path: saved screenshot path (if successful)
	- error: error message (if any)
	"""
	result: Dict[str, Any] = {"opened": False, "captured": False, "saved": False, "path": None, "error": None}

	print(f"[CAMERA] opening device_index={device_index}")
	cap = cv2.VideoCapture(device_index)
	if not cap.isOpened():
		result["error"] = f"Camera not opened (index {device_index})."
		print(f"[CAMERA] ERROR: {result['error']}")
		cap.release()
		return result

	result["opened"] = True

	if resolution:
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

	# Warm up: try reading frames within timeout
	start_t = time.time()
	ok = False
	frame = None
	attempts = 0
	while time.time() - start_t < timeout_sec:
		ok, frame = cap.read()
		attempts += 1
		if ok and frame is not None:
			break
		time.sleep(0.05)

	cap.release()

	if not ok or frame is None:
		result["error"] = f"Failed to read frame within {timeout_sec}s after {attempts} attempts."
		print(f"[CAMERA] ERROR: {result['error']}")
		return result

	result["captured"] = True

	# Save screenshot
	_ensure_dir(out_dir)
	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	out_path = os.path.join(out_dir, f"camera_check_{ts}.png")
	try:
		cv2.imwrite(out_path, frame)
		result["saved"] = True
		result["path"] = out_path
		print(f"[CAMERA] screenshot saved -> {out_path}")
	except Exception as e:
		result["error"] = f"Failed to save screenshot: {e}"
		print(f"[CAMERA] ERROR: {result['error']}")

	return result


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_CAPTURE_DIR = os.path.join(PROJECT_ROOT, "capture")


def capture_once(
	device_index: int = 0,
	resolution: Tuple[int, int] = (1280, 720),
	timeout_sec: float = 5.0,
	out_dir: str | None = None,
	backend: int | None = None,
) -> str:
	"""Capture one frame from the camera and save it.

	Returns the saved image path. Raises RuntimeError on failure.
	"""
	out_dir = out_dir or DEFAULT_CAPTURE_DIR
	_ensure_dir(out_dir)

	# Select backend: param takes precedence, then env var, else default
	if backend is None:
		be_env = os.environ.get("OPENCV_CAPTURE_BACKEND")
		if be_env:
			try:
				backend = int(be_env)
			except Exception:
				backend = None

	cap = cv2.VideoCapture(device_index, backend) if backend is not None else cv2.VideoCapture(device_index)
	if not cap.isOpened():
		cap.release()
		raise RuntimeError(f"Camera not opened (index {device_index})")

	if resolution:
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

	start_t = time.time()
	ok, frame = False, None
	attempts = 0
	while time.time() - start_t < timeout_sec:
		ok, frame = cap.read()
		attempts += 1
		if ok and frame is not None:
			break
		time.sleep(0.05)

	cap.release()

	if not ok or frame is None:
		raise RuntimeError(f"Failed to capture frame within {timeout_sec}s after {attempts} attempts")

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	out_path = os.path.join(out_dir, f"{ts}.png")
	cv2.imwrite(out_path, frame)
	return out_path


__all__ = ["check_camera", "capture_once"]

