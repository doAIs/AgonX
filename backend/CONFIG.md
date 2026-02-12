# 配置管理说明

## 配置文件说明

AgonX 使用 YAML 格式的配置文件，支持多环境配置和环境变量覆盖。

### 配置文件优先级

1. **环境变量** (最高优先级)
   - 环境变量名格式：将配置路径转为大写并用下划线替换点
   - 例如：`mysql.host` → `MYSQL_HOST`

2. **config.local.yaml** (本地配置，不提交到版本控制)
   - 用于本地开发时覆盖默认配置
   - 已添加到 `.gitignore`

3. **config.yaml** (默认配置)
   - 开发环境默认配置

4. **config.prod.yaml** (生产环境配置示例)
   - 生产环境配置模板

## 配置文件结构

```yaml
# 应用基础配置
app:
  name: "AgonX"
  version: "0.1.0"
  debug: true

# API 配置
api:
  v1_prefix: "/api/v1"
  cors_origins:
    - "http://localhost:3001"

# JWT 认证
security:
  secret_key: "your-secret-key"
  algorithm: "HS256"
  access_token_expire_minutes: 1440

# 数据库配置
mysql:
  host: "localhost"
  port: 3306
  user: "agonx"
  password: "agonx_password"
  database: "agonx"

# Redis 配置
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null

# Milvus 向量数据库
milvus:
  host: "localhost"
  port: 19530
  embedding_dimension: 1024

# MinIO 对象存储
minio:
  endpoint: "localhost:19000"
  access_key: "minioadmin"
  secret_key: "minioadmin"
  secure: false
  bucket_name: "agonx-documents"

# Embedding 模型
embedding:
  model: "BAAI/bge-m3"
  device: "cpu"
  cache_folder: "./models"

# LLM 配置
llm:
  default_provider: "openai"
  default_model: "gpt-3.5-turbo"

# 知识库配置
knowledge:
  chunk_size: 512
  chunk_overlap: 50
  top_k: 10
  top_n: 5
  similarity_threshold: 0.7
  search_mode: "hybrid"
  rerank_enabled: true

# 文件上传
upload:
  max_file_size: 52428800  # 50MB
  allowed_extensions:
    - ".pdf"
    - ".txt"
    - ".md"
    - ".doc"
    - ".docx"
```

## 使用方式

### 1. 开发环境

直接使用 `config.yaml`：

```bash
python backend/main.py
```

### 2. 创建本地配置

创建 `backend/config.local.yaml` 覆盖部分配置：

```yaml
# config.local.yaml
mysql:
  host: "192.168.1.100"
  password: "my-local-password"

minio:
  endpoint: "192.168.1.101:9000"
```

### 3. 使用环境变量

```bash
# Linux/Mac
export MYSQL_HOST=192.168.1.100
export MYSQL_PASSWORD=my-password
python backend/main.py

# Windows PowerShell
$env:MYSQL_HOST="192.168.1.100"
$env:MYSQL_PASSWORD="my-password"
python backend/main.py
```

### 4. 生产环境部署

复制生产配置模板：

```bash
cp backend/config.prod.yaml backend/config.yaml
```

编辑 `config.yaml`，将敏感信息使用环境变量：

```yaml
mysql:
  host: "${MYSQL_HOST}"
  password: "${MYSQL_PASSWORD}"

security:
  secret_key: "${JWT_SECRET_KEY}"
```

在生产环境设置环境变量：

```bash
export MYSQL_HOST=prod-mysql.example.com
export MYSQL_PASSWORD=secure-password
export JWT_SECRET_KEY=very-secure-jwt-key
```

## 在代码中使用配置

```python
from backend.app.core.config import settings

# 直接使用
print(settings.MYSQL_HOST)
print(settings.MINIO_ENDPOINT)

# 使用 YAML 配置加载器
from backend.app.core.yaml_config import config

# 获取配置值
mysql_host = config.get("mysql.host")
chunk_size = config.get("knowledge.chunk_size")

# 获取整个配置节
minio_config = config.get_section("minio")
```

## 配置验证

启动应用时会自动验证配置：

```bash
python backend/main.py
```

如果配置文件格式错误或缺失，会抛出异常并提示具体问题。

## 最佳实践

1. ✅ **不要将敏感信息提交到版本控制**
   - 使用 `config.local.yaml` 存储本地敏感配置
   - 生产环境使用环境变量

2. ✅ **使用配置分层**
   - 公共配置写在 `config.yaml`
   - 环境特定配置写在 `config.prod.yaml` 等
   - 个人配置写在 `config.local.yaml`

3. ✅ **配置文档化**
   - 在配置文件中添加注释说明
   - 提供配置示例和默认值

4. ✅ **配置验证**
   - 应用启动时验证必需配置项
   - 对配置值进行类型检查

5. ❌ **避免硬编码**
   - 不要在代码中硬编码配置值
   - 使用配置文件统一管理
