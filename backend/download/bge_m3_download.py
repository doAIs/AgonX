"""
下载 Stable Diffusion 文本生成图片模型
使用优化的下载工具，支持进度显示、断点续传、错误重试等功能
"""

import os
import sys

from backend.download.download_utils import download_model

# 添加项目根目录到路径，以便导入 utils 等模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# 配置参数
REPO_ID = "BAAI/bge-m3"
LOCAL_DIR = os.getenv("LOCAL_MODEL_PATH", "F:\\modules\\bge-m3")

# 可选：只下载必要的文件（取消注释以启用）
# ALLOW_PATTERNS = ["*.safetensors", "*.json", "tokenizer/*", "scheduler/*"]
# IGNORE_PATTERNS = ["*.ckpt", "*.pt", "*fp16*", "*training*"]

if __name__ == "__main__":
    try:
        # 下载模型（使用默认配置，下载所有文件）
        download_model(
            repo_id=REPO_ID,
            local_dir=LOCAL_DIR,
            # allow_patterns=ALLOW_PATTERNS,  # 取消注释以只下载指定文件
            # ignore_patterns=IGNORE_PATTERNS,  # 取消注释以忽略指定文件
            max_workers=16,  # 多线程加速
            force_download=False,  # 默认自动断点续传，设为True强制重新下载
            check_before_download=True,  # 下载前检查本地是否已存在
            retry_times=3  # 失败重试次数
        )
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        sys.exit(1)
