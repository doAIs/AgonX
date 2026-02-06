# AgonX - 多智能体协作平台

AgonX 是一款面向未来的多智能体协作平台，基于 **Vue 3** 和 **FastAPI** 构建。它集成了 **LangGraph** 智能体编排、**Milvus** 向量知识库、以及深度的上下文记忆系统，旨在通过多个专业智能体的协同工作来解决复杂的任务。

---

## 🌟 核心特性

- **多智能体协作**: 基于 LangGraph 实现 `Researcher`、`Analyzer`、`Responder` 三智能体流水线协作。
- **混合记忆系统**:
  - **短期记忆**: 基于 Redis 存储，保留会话上下文。
  - **长期记忆**: 基于 Milvus 语义检索，记住用户偏好与关键历史。
- **专业级知识库**:
  - 支持多格式（PDF, Word, TXT, MD）上传。
  - 基于 BGE-M3 的混合检索（向量 + 关键词）及重排序（Rerank）。
  - 可配置的分块策略与检索参数。
- **多模型支持**: 集成 Qwen3, DeepSeek, GLM-4 等主流大模型，支持 API Key 灵活配置。
- **多媒体处理**: 支持 MinIO 存储图片，前端自动渲染检索到的关联素材。
- **商业化就绪**: 预留多租户、RBAC 权限、计费计量接口，代码结构专业且易于扩展。
- **结果导出**: 支持将会话或检索结果一键导出为 PDF 文件。

---

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 (Composition API) + TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **样式**: CSS 变量 + 暗色科技风设计

### 后端
- **框架**: FastAPI (Python 3.11+)
- **智能体编排**: LangGraph + LangChain
- **数据库**: MySQL 8.0 (结构化数据)
- **向量库**: Milvus 2.x
- **缓存/短期记忆**: Redis 7.x
- **对象存储**: MinIO
- **模型调用**: OpenAI SDK (兼容模式)

---

## 📂 项目结构

```text
AgonX/
├── frontend/                 # Vue3 前端源码
│   ├── src/api/             # API 接口封装
│   ├── src/stores/          # Pinia 状态管理
│   ├── src/views/           # 页面视图 (含登录粒子动效)
│   └── nginx.conf           # 生产环境 Nginx 配置
├── backend/                  # FastAPI 后端源码
│   ├── app/agents/          # LangGraph 智能体逻辑
│   ├── app/knowledge/       # 知识库与 RAG 逻辑
│   ├── app/memory/          # 长短期记忆管理器
│   ├── app/models/          # SQLAlchemy 数据库模型
│   └── main.py              # 应用入口
├── docker/                   # Docker 配置文件
│   └── mysql/init.sql       # 数据库初始化脚本
└── docker-compose.yml        # 一键编排脚本
```

---

## 🚀 快速开始

### 1. 环境要求
- Docker & Docker Compose
- Node.js 20+ (仅本地开发需要)
- Python 3.11+ (仅本地开发需要)

### 2. 启动服务 (推荐方式)
```bash
# 克隆仓库
git clone https://github.com/your-username/AgonX.git
cd AgonX

# 启动所有服务 (Frontend, Backend, MySQL, Redis, Milvus, MinIO)
docker-compose up -d
```

### 3. 本地开发调试
- **前端**: `cd frontend && npm install && npm run dev` (访问 http://localhost:3000)
- **后端**: `cd backend && pip install -r requirements.txt && python main.py` (访问 http://localhost:8080/docs)

**注意**：本地开发环境后端使用 **8080 端口**，Docker 容器环境使用 **8000 端口**，避免端口冲突。

---

## 🔐 默认账号与凭证

### 应用登录账号
- **用户名**: `admin`
- **密码**: `admin123`

### MySQL 数据库
- **数据库名**: `agonx`
- **用户名**: `agonx`
- **密码**: `agonx_password`
- **Root 密码**: `root_password`
- **端口**: `3306`

### MinIO 对象存储
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin`
- **控制台端口**: `9001`
- **API 端口**: `9000`

### Redis
- **端口**: `6379`
- **密码**: 无

### Milvus 向量数据库
- **端口**: `19530`
- **管理端口**: `9091`

---

## 🎨 界面设计亮点

- **科技感 UI**: 采用暗色背景结合紫色渐变（Cyberpunk 风格），提升视觉冲击力。
- **粒子动效**: 登录页面集成动态粒子背景，增加产品交互深度。
- **可视化架构**: 在智能体管理页面通过流程图直观展示 Agent 协作链路。

---

## 📜 许可证

本项目基于 [MIT License](LICENSE) 开源。
