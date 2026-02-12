"""
配置模块
从 YAML 文件和环境变量加载配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from backend.app.core.yaml_config import config as yaml_config


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = yaml_config.get("app.name", "AgonX")
    APP_VERSION: str = yaml_config.get("app.version", "0.1.0")
    DEBUG: bool = yaml_config.get("app.debug", True)
    
    # API配置
    API_V1_PREFIX: str = yaml_config.get("api.v1_prefix", "/api/v1")
    
    # JWT配置
    SECRET_KEY: str = yaml_config.get("security.secret_key", "your-super-secret-key-change-in-production")
    ALGORITHM: str = yaml_config.get("security.algorithm", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(yaml_config.get("security.access_token_expire_minutes", 1440))
    
    # MySQL配置
    MYSQL_HOST: str = yaml_config.get("mysql.host", "127.0.0.1")
    MYSQL_PORT: int = int(yaml_config.get("mysql.port", 3306))
    MYSQL_USER: str = yaml_config.get("mysql.user", "root")
    MYSQL_PASSWORD: str = yaml_config.get("mysql.password", "password")
    MYSQL_DATABASE: str = yaml_config.get("mysql.database", "agonx")
    
    @property
    def MYSQL_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def MYSQL_URL_SYNC(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # Redis配置
    REDIS_HOST: str = yaml_config.get("redis.host", "localhost")
    REDIS_PORT: int = int(yaml_config.get("redis.port", 6379))
    REDIS_PASSWORD: Optional[str] = yaml_config.get("redis.password", None)
    REDIS_DB: int = int(yaml_config.get("redis.db", 0))
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Milvus配置
    MILVUS_HOST: str = yaml_config.get("milvus.host", "localhost")
    MILVUS_PORT: int = int(yaml_config.get("milvus.port", 19530))
    MILVUS_USER: str = yaml_config.get("milvus.user", "")
    MILVUS_PASSWORD: str = yaml_config.get("milvus.password", "")
    EMBEDDING_DIMENSION: int = int(yaml_config.get("milvus.embedding_dimension", 1024))
    
    # MinIO配置
    MINIO_ENDPOINT: str = yaml_config.get("minio.endpoint", "localhost:19000")
    MINIO_ACCESS_KEY: str = yaml_config.get("minio.access_key", "minioadmin")
    MINIO_SECRET_KEY: str = yaml_config.get("minio.secret_key", "minioadmin")
    MINIO_BUCKET: str = yaml_config.get("minio.bucket_name", "agonx-documents")
    MINIO_SECURE: bool = yaml_config.get("minio.secure", False)
    
    # LLM配置 (默认)
    DEFAULT_LLM_PROVIDER: str = yaml_config.get("llm.default_provider", "qwen")
    DEFAULT_LLM_MODEL: str = yaml_config.get("llm.default_model", "qwen-max")
    DEFAULT_LLM_API_KEY: str = yaml_config.get("llm.api_key", "")
    DEFAULT_LLM_BASE_URL: str = yaml_config.get("providers.qwen.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # Embedding配置
    DEFAULT_EMBEDDING_MODEL: str = yaml_config.get("embedding.model", "BAAI/bge-m3")
    EMBEDDING_MODEL: str = yaml_config.get("embedding.model", "BAAI/bge-m3")  # 兼容旧代码
    EMBEDDING_DEVICE: str = yaml_config.get("embedding.device", "cpu")
    EMBEDDING_CACHE_FOLDER: str = yaml_config.get("embedding.cache_folder", "./models")
    EMBEDDING_DIMENSION: int = int(yaml_config.get("embedding.dimension", 1024))
    
    # 知识库默认配置
    DEFAULT_CHUNK_SIZE: int = int(yaml_config.get("knowledge.chunk_size", 512))
    DEFAULT_CHUNK_OVERLAP: int = int(yaml_config.get("knowledge.chunk_overlap", 50))
    DEFAULT_TOP_K: int = int(yaml_config.get("knowledge.top_k", 10))
    DEFAULT_TOP_N: int = int(yaml_config.get("knowledge.top_n", 5))
    DEFAULT_SIMILARITY_THRESHOLD: float = float(yaml_config.get("knowledge.similarity_threshold", 0.7))
    
    # 文件上传配置
    MAX_FILE_SIZE: int = int(yaml_config.get("upload.max_file_size", 52428800))
    
    # 记忆配置
    SHORT_TERM_MEMORY_TTL: int = 3600  # 1小时
    SHORT_TERM_MEMORY_MAX_MESSAGES: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
