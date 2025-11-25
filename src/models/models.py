import torch
import torch.nn as nn

class BasicBlock1D(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.downsample = None
        if stride != 1 or in_channels != out_channels:
            self.downsample = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm1d(out_channels)
            )
    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        out = self.relu(out)
        return out

class ResNet1D(nn.Module):
    def __init__(self, input_dim, output_dim, base_channels=32, layers=[2,2,2]):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.base_channels = base_channels
        self.conv1 = nn.Conv1d(1, base_channels, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(base_channels)
        self.relu = nn.ReLU(inplace=True)
        self.layer1 = self._make_layer(base_channels, base_channels, layers[0])
        self.layer2 = self._make_layer(base_channels, base_channels*2, layers[1], stride=2)
        self.layer3 = self._make_layer(base_channels*2, base_channels*4, layers[2], stride=2)
        self.gap = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(base_channels*4, output_dim)
    def _make_layer(self, in_channels, out_channels, blocks, stride=1):
        layers = [BasicBlock1D(in_channels, out_channels, stride)]
        for _ in range(1, blocks):
            layers.append(BasicBlock1D(out_channels, out_channels))
        return nn.Sequential(*layers)
    def forward(self, x):
        # x: (batch, input_dim) -> (batch, 1, input_dim)
        x = x.unsqueeze(1)
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.gap(out)
        out = out.view(out.size(0), -1)
        out = self.fc(out)
        return out