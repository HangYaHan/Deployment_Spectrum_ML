import os
import torch
import numpy as np
from typing import List, Dict, Any
from .models import ResNet1D

class ModelLoadError(Exception):
    """模型加载失败异常"""
    pass

class ModelLoader:
    def __init__(self, model_dir: str = "src/models"):
        """
        初始化模型加载器
        Args:
            model_dir: 模型文件所在的目录，默认 'src/models'
        """
        # 转换为绝对路径以避免相对路径问题
        if not os.path.isabs(model_dir):
            model_dir = os.path.abspath(model_dir)
            
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "model.pth")
        self.mean_path = os.path.join(model_dir, "input_mean.npy")
        self.std_path = os.path.join(model_dir, "input_std.npy")
        
        self.model = None
        self.input_mean = None
        self.input_std = None
        self.device = torch.device("cpu") # 默认使用 CPU

    def load(self) -> None:
        """加载模型权重和预处理参数"""
        if not os.path.exists(self.model_path):
            raise ModelLoadError(f"Model file not found: {self.model_path}")
        
        try:
            # 加载预处理参数
            if os.path.exists(self.mean_path):
                self.input_mean = np.load(self.mean_path)
            else:
                raise ModelLoadError(f"Mean file not found: {self.mean_path}")
                
            if os.path.exists(self.std_path):
                self.input_std = np.load(self.std_path)
            else:
                raise ModelLoadError(f"Std file not found: {self.std_path}")
            
            # 检查维度以初始化模型
            input_dim = self.input_mean.shape[0]
            
            # 加载 state_dict
            state_dict = torch.load(self.model_path, map_location=self.device)
            
            # 推断 output_dim
            if 'fc.weight' in state_dict:
                output_dim = state_dict['fc.weight'].shape[0]
            else:
                # 默认值，如果无法推断
                output_dim = 255 
            
            # 初始化模型结构
            self.model = ResNet1D(input_dim=input_dim, output_dim=output_dim)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            
            # print(f"[ModelLoader] Loaded model from {self.model_path}")
            # print(f"[ModelLoader] Input dim: {input_dim}, Output dim: {output_dim}")
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {e}")

    def predict(self, features: List[float]) -> Dict[str, List[float]]:
        """
        执行推理
        Args:
            features: 灰度特征列表 (长度应等于 input_dim)
        Returns:
            Dict with 'wavelengths' and 'intensities'
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        if len(features) != self.input_mean.shape[0]:
             raise ValueError(f"Input features dimension mismatch. Expected {self.input_mean.shape[0]}, got {len(features)}")

        try:
            # 预处理: (x - mean) / std
            x = np.array(features, dtype=np.float32)
            x = (x - self.input_mean) / (self.input_std + 1e-6)
            
            # 转换为 Tensor: (1, input_dim)
            x_tensor = torch.from_numpy(x).unsqueeze(0).to(self.device)
            
            # 推理
            with torch.no_grad():
                output = self.model(x_tensor)
                
            intensities = output.squeeze(0).cpu().numpy().tolist()
            
            # 生成波长
            # TODO: 如果有真实的波长校准文件，应从文件中读取
            # 这里假设输出对应 400nm 到 1000nm 的线性分布
            wavelengths = np.linspace(400, 1000, len(intensities)).tolist()
            
            return {
                "wavelengths": wavelengths,
                "intensities": intensities
            }
            
        except Exception as e:
            # 可以在这里记录日志
            raise e
