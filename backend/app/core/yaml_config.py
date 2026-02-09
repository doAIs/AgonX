"""
YAML 配置加载器
支持从 YAML 文件和环境变量加载配置
"""
import os
import yaml
from typing import Any, Dict
from pathlib import Path


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 配置文件在 backend/ 目录下
        config_path = Path(__file__).parent.parent.parent / self.config_file
        
        # 优先加载 config.local.yaml（本地配置）
        local_config_path = Path(__file__).parent.parent.parent / "config.local.yaml"
        if local_config_path.exists():
            config_path = local_config_path
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持嵌套键（用.分隔）
        优先从环境变量读取，环境变量名为大写并用_替换.
        
        Example:
            config.get("mysql.host") 
            会先查找环境变量 MYSQL_HOST，如果没有则从 YAML 读取
        """
        # 尝试从环境变量读取
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # 从 YAML 配置读取
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节"""
        return self._config.get(section, {})
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局配置实例
config = ConfigLoader()
