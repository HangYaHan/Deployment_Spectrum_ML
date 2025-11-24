# 系统总览

本系统用于在树莓派环境中，通过按键交互触发相机采集，结合预定义 ROI（Region of Interest）区域统计灰度特征，调用光谱预测模型并在显示屏上实时呈现结果。该文档描述主流程、数据流、模块职责与接口设计，便于后续扩展与实现保持一致。

## 主循环简述

1. 监听按钮状态（轮询或中断）。
2. 检测到按下事件后：
   - 触发相机拍摄一帧原始图像（RawImage）。
   - 读取本地 ROI 定义。
   - 计算各 ROI 平均灰度。
   - 将统计向量传入模型进行光谱预测（SpectrumPrediction）。
   - 在屏幕上绘制光谱曲线+文本状态。 
3. 进入下一次循环，继续监听。

## 关键数据对象
- RawImage：原始图像（建议使用 `numpy.ndarray` 或 OpenCV Mat）。
- ROI 定义：`[{"name": str, "x": int, "y": int, "w": int, "h": int}]`。
- ROIStats：`{"name": str, "mean_gray": float}` 列表；或直接组合成特征向量 `features: List[float]`。
- SpectrumPrediction：`{"wavelengths": List[float], "intensities": List[float]}`。
- RenderPayload：封装要绘制的光谱数据、标题、状态文本。

## 模块设计与职责

| 模块              | 目录                       | 职责                               | 备注                         |
| ----------------- | -------------------------- | ---------------------------------- | ---------------------------- |
| 按钮 Button       | `system/` 或独立 `button/` | 读取按钮当前状态（是否按下）       | 可抽象硬件层，便于模拟测试   |
| 相机 Camera       | `camera/`                  | 初始化硬件，采集单帧图像           | 需处理分辨率、曝光、失败重试 |
| 模型 Models       | `models/`                  | 加载光谱预测模型，执行推理         | 支持离线文件或导出的轻量模型 |
| 显示屏 Screen     | `screen/`                  | 绘制光谱曲线、文本、可能的图像缩略 | 考虑刷新率与缓存             |
| 系统主循环 System | `system/`                  | 协调整体流程、调度各模块并处理异常 | 提供 `run()` / `step()` 方法 |
| 测试 Test         | `test/`                    | 针对各模块单测、集成测试           | 使用 pytest 或 unittest      |

## 5. 接口草案（Python 伪代码）

```python
# button/interface.py
class Button:
	def __init__(self, pin: int):
		...
	def is_pressed(self) -> bool:
		"""返回按钮是否被按下"""
		...

# camera/camera.py
class Camera:
	def __init__(self, device_index: int = 0, resolution=(640, 480)):
		...
	def initialize(self) -> None:
		...
	def capture_frame(self) -> "RawImage":
		...  #  CameraError if capture fails

# models/loader.py
class ModelLoader:
	def __init__(self, model_path: str):
		...
	def load(self) -> None:
		...
	def predict(self, features: list[float]) -> "SpectrumPrediction":
		...

# screen/display.py
class Display:
	def __init__(self, size=(800, 480)):
		...
	def clear(self) -> None: ...
	def plot_spectrum(self, prediction: "SpectrumPrediction") -> None:
		...
	def show_status(self, text: str) -> None:
		...

# system/main_loop.py
class MainLoop:
	def __init__(self, button: Button, camera: Camera, model: ModelLoader, display: Display, roi_config_path: str):
		...
	def load_rois(self) -> list[dict]:
		...
	def compute_features(self, image: "RawImage", rois: list[dict]) -> list[float]:
		...
	def step(self) -> None:
		"""
		执行一次循环：检测按钮 -> 采集 -> 计算特征 -> 预测 -> 显示"""
		...
	def run(self) -> None:
		while True:
			self.step()
```

## 错误与异常策略
- CameraError：硬件初始化或采集失败；重试 N 次后记录日志。
- ModelNotLoadedError：在调用 `predict` 前未加载模型。
- DisplayError：绘制失败（例如驱动异常），可降级为文本提示。

## 日志与可观测性建议
- 关键阶段：按钮事件、图像采集时间、ROI 特征向量、模型推理耗时、显示刷新。
- 可选写入 CSV：`timestamp, roi_means..., spectrum_hash, latency_ms`。