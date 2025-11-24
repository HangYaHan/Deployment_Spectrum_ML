**系统实现计划（已润色**

本计划给出从最小可运行原型到可测试、可扩展部署的分步路线。每一项任务包含：目标描述、精确实现指标（可测量）、建议接口签名与验收测试思路。目标是把当前仓库变为模块化、可测试并且易于扩展的工程化项目。

**总体分阶段目标**
- **阶段 0（现状检查）**：确保仓库能在本地导入不报错；可运行现有单元测试（若存在）。
- **阶段 1（模块化 + 单元测试）**：为 Button/Camera/Model/Display/System 提供抽象接口并实现单元测试。
- **阶段 2（集成 + 性能）**：完成主循环集成测试，收集并优化关键路径耗时。

**任务清单（含实现指标 & 接口）**

1. **按钮模块（Button）**
	 - 目标：可靠检测按键事件并可在单元测试中替换为模拟实现。
	 - 实现指标：
		 - `is_pressed()` 返回 `bool`。模拟模式下支持预设事件序列。
		 - 轮询实现响应延迟 < 50 ms；中断实现近乎实时。
	 - Python 接口示例：
		 - `class Button:
				 def __init__(self, pin: int, simulate: bool = False): ...
				 def is_pressed(self) -> bool: ...
				 def wait_for_press(self, timeout: float | None = None) -> bool: ...`
	 - 验收测试：通过注入模拟实现测试 `wait_for_press` 行为；真实硬件上连续按 10 次，漏判 <=1 次。

2. **相机模块（Camera）**
	 - 目标：提供稳定的单帧采集接口并支持失败重试。
	 - 实现指标：
		 - `capture_frame()` 返回 `numpy.ndarray`（灰度或 BGR）或抛出 `CameraError`。
		 - 单帧采集中位延迟目标 < 200 ms（树莓派参考），默认重试次数 3。
	 - Python 接口示例：
		 - `class Camera:
				 def __init__(self, device_index: int = 0, resolution: tuple[int,int] = (640,480)): ...
				 def initialize(self) -> None: ...
				 def capture_frame(self) -> numpy.ndarray: ...
				 def close(self) -> None: ...`
	 - 验收测试：使用 Mock 返回已知数组并比对 ROI 计算结果；真实硬件上 10 次采样成功率 >= 90%。

3. **ROI 定义与特征计算（utils/roi）**
	 - 目标：统一 ROI 配置格式并提供准确、可测试的特征计算函数。
	 - 数据格式：`[{"name": str, "x": int, "y": int, "w": int, "h": int}]`。
	 - 接口示例：
		 - `def load_rois(path: str) -> list[dict]: ...`
		 - `def compute_roi_features(image: numpy.ndarray, rois: list[dict]) -> list[float]: ...`
	 - 验收测试：构造固定灰度矩阵，断言 `compute_roi_features` 的均值与期望误差 < 1e-6。

4. **模型模块（ModelLoader / Predictor）**
	 - 目标：可靠加载模型并在可接受延迟内提供推理服务。
	 - 实现指标：
		 - `load()` 完成时间目标 2 s（小模型）；加载失败抛出 `ModelLoadError`。
		 - `predict(features: list[float]) -> dict`（返回 `{'wavelengths': [...], 'intensities': [...]}`），端到端延迟目标 < 200 ms（视模型大小可放宽）。
	 - 接口示例：
		 - `class ModelLoader:
				 def __init__(self, model_path: str): ...
				 def load(self) -> None: ...
				 def predict(self, features: list[float]) -> dict: ...`
	 - 验收测试：使用 Mock 模型或固定权值模型，输入特征得到确定性输出；路径错误应抛 `ModelLoadError`。

5. **显示模块（Display / Screen）**
	 - 目标：在屏幕上绘制光谱曲线与状态文本，API 需支持非阻塞或快速返回。
	 - 实现指标：
		 - `plot_spectrum(prediction)` 返回时间目标 < 100 ms（绘制调度）。
		 - `clear()` 能清空并显示状态提示。
	 - 接口示例：
		 - `class Display:
				 def __init__(self, size: tuple[int,int]): ...
				 def plot_spectrum(self, prediction: dict, title: str | None = None) -> None: ...
				 def show_status(self, text: str) -> None: ...
				 def close(self) -> None: ...`
	 - 验收测试：模拟环境断言绘制调用；真实屏幕使用截图或视觉检查确认输出。

6. **主循环（MainLoop）**
	 - 目标：整合各模块，保证端到端流程稳定并产出 Telemetry。
	 - 实现指标：
		 - 单次完整流程平均延迟目标 < 1 s（依平台可放宽）。
		 - 异常时有明确回退（例如显示错误提示、重试或返回安全状态），并写入日志。
	 - 接口示例：
		 - `class MainLoop:
				 def __init__(self, button, camera, model, display, roi_path: str): ...
				 def step(self) -> dict:  # 返回 telemetry，如 timings、status
				 def run(self) -> None: ...`
	 - 验收测试：使用 Mock 组件执行 100 次 `step()`，成功率 >= 95%；输出各阶段平均耗时。