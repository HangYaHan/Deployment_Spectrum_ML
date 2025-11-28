"""
GPIOZERO 版：树莓派 6 按钮调试脚本（无需传参，直接运行）

前置准备（在树莓派上执行）：
  sudo apt update && sudo apt upgrade -y
  sudo apt install python3-pip -y
  sudo pip3 install gpiozero
  # 如果使用某些低级功能可能需要 pigpio：
  # sudo apt install pigpio python3-pigpio
  # sudo systemctl enable --now pigpiod

运行：
  sudo python3 src/test/test_button.py

说明：脚本使用 `gpiozero.Button` 的 `bounce_time` 与 `hold_time` 功能进行去抖与长按检测，
在非 Raspberry Pi 环境会回退到模拟模式以便本地开发测试。
"""

from __future__ import annotations

import time
import random
from typing import Dict, Optional, List

try:
	from gpiozero import Button
	ON_RPI = True
except Exception:
	ON_RPI = False


# 默认 6 个 BCM 引脚
DEFAULT_PINS: List[int] = [4, 17, 27, 22, 5, 6]


class ButtonStats:
	def __init__(self, pin: int):
		self.pin = pin
		self.count = 0
		self.last_duration: Optional[float] = None
		self._pressed_at: Optional[float] = None

	def on_press(self):
		self._pressed_at = time.time()
		print(f"[EVENT] pin {self.pin} PRESSED at {time.strftime('%H:%M:%S')}")

	def on_release(self):
		if self._pressed_at is None:
			return
		duration = time.time() - self._pressed_at
		self.last_duration = duration
		self.count += 1
		kind = "LONG" if duration >= 1.0 else "SHORT"
		print(f"[EVENT] pin {self.pin} RELEASED at {time.strftime('%H:%M:%S')}, duration={duration:.3f}s ({kind}), total_count={self.count}")
		self._pressed_at = None

	def on_hold(self):
		print(f"[EVENT] pin {self.pin} HELD (hold event at {time.strftime('%H:%M:%S')})")


def run_with_gpiozero(pins: List[int], bounce_time: float = 0.05, hold_time: float = 1.0) -> None:
	"""使用 gpiozero 监听按钮事件"""
	stats: Dict[int, ButtonStats] = {p: ButtonStats(p) for p in pins}

	buttons = []
	for p in pins:
		btn = Button(p, pull_up=True, bounce_time=bounce_time, hold_time=hold_time)
		s = stats[p]
		btn.when_pressed = s.on_press
		btn.when_released = s.on_release
		btn.when_held = s.on_hold
		buttons.append(btn)

	print(f"[MONITOR] Listening on pins: {pins} using gpiozero. Press Ctrl-C to stop.")
	try:
		while True:
			time.sleep(1.0)
	except KeyboardInterrupt:
		print("\n[MONITOR] Stopping...")
	finally:
		print_summary(stats)


def run_simulator(pins: List[int]) -> None:
	"""在非树莓派环境下的简单模拟器，用随机事件代替真实按键。"""
	stats: Dict[int, ButtonStats] = {p: ButtonStats(p) for p in pins}
	print("[SIM] Running simulator mode. Press Ctrl-C to stop.")
	try:
		while True:
			p = random.choice(pins)
			s = stats[p]
			s.on_press()
			# 随机持续 50-800 ms 或更长表示长按
			dur = random.uniform(0.05, 1.5)
			time.sleep(dur)
			s.on_release()
			time.sleep(random.uniform(0.2, 1.5))
	except KeyboardInterrupt:
		print("\n[SIM] Stopping simulator...")
	finally:
		print_summary(stats)


def print_summary(stats: Dict[int, ButtonStats]) -> None:
	print("\n[SUMMARY] Button press summary:")
	for p, s in stats.items():
		print(f"  pin {p}: presses={s.count}, last_duration={s.last_duration}")


def main() -> None:
	pins = DEFAULT_PINS
	if ON_RPI:
		print("[ENV] gpiozero available — running on Raspberry Pi (or gpiozero installed)")
		run_with_gpiozero(pins)
	else:
		print("[ENV] gpiozero not available — running in simulator mode")
		run_simulator(pins)


if __name__ == "__main__":
	main()

