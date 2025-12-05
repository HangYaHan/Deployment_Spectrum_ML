"""
Model inspection utilities for testing availability of model assets.

Provides:
- check_model(model_dir='src/models', device='cpu') -> dict
  Loads input mean/std and model weights, prints summary, and returns details.
"""

from typing import Any, Dict, Optional
import os
import numpy as np


def _load_numpy_array(path: str) -> tuple[Optional[np.ndarray], Optional[str]]:
    try:
        arr = np.load(path)
        return arr, None
    except Exception as e:
        return None, f"numpy load error for {os.path.basename(path)}: {e}"


def _extract_state_dict(obj: Any) -> tuple[Optional[dict], Optional[str]]:
    try:
        # If it's a torch module
        if hasattr(obj, "state_dict") and callable(getattr(obj, "state_dict")):
            return obj.state_dict(), None
        # If it's a mapping-like checkpoint
        if isinstance(obj, dict):
            if "state_dict" in obj and isinstance(obj["state_dict"], dict):
                return obj["state_dict"], None
            return obj, None
        return None, "unsupported model object type"
    except Exception as e:
        return None, f"state_dict extract error: {e}"


def check_model(model_dir: str = os.path.join("src", "models"), device: str = "cpu") -> Dict[str, Any]:
    """Check model assets: input_mean.npy, input_std.npy, and model.pth.

    Returns dict with keys:
    - mean_shape, std_shape: shapes if arrays load
    - fc_weight_shape: shape if fc.weight present
    - keys_sample: list of up to 10 keys from state dict
    - ok: overall success boolean
    - errors: list of error strings if any
    """
    result: Dict[str, Any] = {
        "mean_shape": None,
        "std_shape": None,
        "fc_weight_shape": None,
        "keys_sample": [],
        "ok": False,
        "errors": [],
    }

    mean_path = os.path.join(model_dir, "input_mean.npy")
    std_path = os.path.join(model_dir, "input_std.npy")
    model_path = os.path.join(model_dir, "model.pth")

    mean, err = _load_numpy_array(mean_path)
    if err:
        print(f"[MODEL] {err}")
        result["errors"].append(err)
    else:
        print(f"[MODEL] Mean shape: {getattr(mean, 'shape', None)}")
        result["mean_shape"] = getattr(mean, "shape", None)

    std, err = _load_numpy_array(std_path)
    if err:
        print(f"[MODEL] {err}")
        result["errors"].append(err)
    else:
        print(f"[MODEL] Std shape: {getattr(std, 'shape', None)}")
        result["std_shape"] = getattr(std, "shape", None)

    try:
        import torch  # local import to avoid hard dependency at import time
        map_loc = "cpu" if device == "cpu" else device
        obj = torch.load(model_path, map_location=map_loc)
        state_dict, sderr = _extract_state_dict(obj)
        if sderr:
            print(f"[MODEL] {sderr}")
            result["errors"].append(sderr)
        elif isinstance(state_dict, dict):
            keys = list(state_dict.keys())
            result["keys_sample"] = keys[:10]
            if "fc.weight" in state_dict:
                try:
                    result["fc_weight_shape"] = tuple(state_dict["fc.weight"].shape)  # type: ignore[attr-defined]
                    print(f"[MODEL] FC weight shape: {result['fc_weight_shape']}")
                except Exception:
                    print("[MODEL] FC weight present but shape not readable")
            else:
                print("[MODEL] fc.weight not found in state_dict")
        else:
            result["errors"].append("state_dict not available")
    except Exception as e:
        msg = f"torch/model load error: {e}"
        print(f"[MODEL] {msg}")
        result["errors"].append(msg)

    result["ok"] = (
        result["mean_shape"] is not None
        and result["std_shape"] is not None
        and (result["keys_sample"] or result["fc_weight_shape"] is not None)
    )
    return result


__all__ = ["check_model"]

# ===== Reconstruction pipeline =====
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import glob


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CAPTURE_DIR = os.path.join(PROJECT_ROOT, "capture")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")
MODELS_DIR = os.path.join(PROJECT_ROOT, "src", "models")
ROIS_FILE = os.path.join(MODELS_DIR, "rois.txt")
BGROIS_FILE = os.path.join(MODELS_DIR, "bgrois.txt")


def _list_captures() -> list[str]:
    return sorted(glob.glob(os.path.join(CAPTURE_DIR, "*.png")) +
                  glob.glob(os.path.join(CAPTURE_DIR, "*.jpg")) +
                  glob.glob(os.path.join(CAPTURE_DIR, "*.jpeg")))


def _latest_capture() -> str | None:
    files = _list_captures()
    if not files:
        return None
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def _parse_roi_line(line: str) -> tuple[int, int, int, int] | None:
    parts = [s.strip() for s in line.replace("\t", ",").replace(" ", ",").split(",") if s.strip()]
    if len(parts) < 4:
        return None
    try:
        x, y, w, h = map(int, parts[:4])
        return x, y, w, h
    except Exception:
        return None


def _load_rois(path: str, limit: int | None = None) -> list[tuple[int, int, int, int]]:
    rois: list[tuple[int, int, int, int]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = _parse_roi_line(line)
            if r:
                rois.append(r)
            if limit and len(rois) >= limit:
                break
    return rois


def _compute_roi_mean_gray(img_gray: np.ndarray, roi: tuple[int, int, int, int]) -> float:
    x, y, w, h = roi
    H, W = img_gray.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = img_gray[y0:y1, x0:x1]
    return float(np.mean(patch))


def reconstruct_latest() -> str:
    """Reconstruct spectrum from the latest capture and save a plot.

    Returns path to the saved spectrum PNG.
    """
    img_path = _latest_capture()
    if not img_path:
        raise RuntimeError("No capture found. Please run 'capture' first.")

    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"Failed to read image: {img_path}")
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Background ROI factor: use the 5th value from bgrois.txt (single line is expected)
    if not os.path.exists(BGROIS_FILE):
        raise FileNotFoundError(BGROIS_FILE)
    with open(BGROIS_FILE, "r", encoding="utf-8", errors="ignore") as f:
        line = f.readline().strip()
    parts = [s.strip() for s in line.replace("\t", ",").replace(" ", ",").split(",") if s.strip()]
    if len(parts) < 5:
        raise RuntimeError("bgrois.txt must contain at least 5 values (xywh,value)")
    try:
        bg_value = float(parts[4])
    except Exception as e:
        raise RuntimeError(f"Invalid bg value in bgrois.txt: {e}")
    if bg_value == 0:
        bg_value = 1e-6

    # Foreground ROIs: need 32 average gray values
    if not os.path.exists(ROIS_FILE):
        raise FileNotFoundError(ROIS_FILE)
    fg_list = _load_rois(ROIS_FILE, limit=32)
    if len(fg_list) < 32:
        raise RuntimeError(f"ROIs insufficient: need 32, got {len(fg_list)}")

    roi_means = [_compute_roi_mean_gray(img_gray, r) for r in fg_list]
    features = [(v / bg_value) for v in roi_means]

    # Standardize features using input_mean/std
    mean_path = os.path.join(MODELS_DIR, "input_mean.npy")
    std_path = os.path.join(MODELS_DIR, "input_std.npy")
    mean, err = _load_numpy_array(mean_path)
    if err or mean is None:
        raise RuntimeError(f"Failed to load input_mean.npy: {err}")
    std, err = _load_numpy_array(std_path)
    if err or std is None:
        raise RuntimeError(f"Failed to load input_std.npy: {err}")
    if mean.shape[0] != 32 or std.shape[0] != 32:
        raise RuntimeError("input_mean/std must have shape (32,)")
    x = (np.array(features, dtype=np.float32) - mean.astype(np.float32)) / (std.astype(np.float32) + 1e-6)

    # Inference using ModelLoader
    try:
        from src.models.model_loader import ModelLoader
        loader = ModelLoader(model_dir=MODELS_DIR)
        loader.load()
        result = loader.predict(x.tolist())
    except Exception as e:
        raise RuntimeError(f"Model inference error: {e}")

    intensities = result.get("intensities", [])
    if not intensities:
        raise RuntimeError("Model returned empty intensities")
    wavelengths = result.get("wavelengths") or list(range(400, 400 + len(intensities)))

    # Ensure result directory exists and save plot there
    os.makedirs(RESULT_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(img_path))[0]
    out_png = os.path.join(RESULT_DIR, f"{base}_spectrum.png")
    plt.figure(figsize=(10, 4))
    plt.plot(wavelengths, intensities, lw=1.5)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Intensity")
    plt.title(f"Spectrum - {base}")
    plt.grid(True, ls=":", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

    print(f"[RECONSTRUCT] Saved spectrum plot -> {out_png}")
    return out_png


__all__.extend(["reconstruct_latest"])

