# AI_Art:把游戏图片转成 2.5D 现代卡通风

**这个目录在游戏项目之外,不会被打包进游戏。**

## 目录
| 目录 | 用途 |
|---|---|
| `ComfyUI/` | 出图软件(已装好)和模型(`ComfyUI/models/`) |
| `venv/` | 专用的 Python 环境(装了 PyTorch 等,不要动) |
| `input_original/` | 要转换的原图(从游戏里复制进来的**副本**) |
| `reference_style/` | 风格参考图:放你想要的"现代卡通 2.5D"样图 |
| `output_25d/` | 转换后的新图(不会自动覆盖游戏里的图) |
| `scripts/` | 批处理脚本 |
| `logs/` | 安装和运行日志 |
| `start_comfyui.bat` | 双击启动 ComfyUI |

## 已安装
- ComfyUI + PyTorch 2.x(CUDA 12.8,识别到 RTX 4060 8GB)
- 模型:SDXL 1.0 底模、ControlNet Union(promax)、IP-Adapter Plus(SDXL)和对应的 CLIP 图像编码器
- 扩展:ComfyUI_IPAdapter_plus、comfyui_controlnet_aux

## 做法(图生图 + 保形状 + 统一风格)
1. 原图作为输入;ControlNet 用线稿或深度锁住形状;IP-Adapter 用你的**风格参考图**统一画风。
2. 重绘强度约 0.4 到 0.6:越小越像原图,越大风格越强但形状越容易变。
3. 批量时固定提示词、种子和参数,风格才会一致。

## 授权提醒(上架前自己核对原文)
- SDXL 1.0:CreativeML Open RAIL++-M,允许商用但有使用限制。
- IP-Adapter、ControlNet 各自的授权也要看对应的模型页面。
