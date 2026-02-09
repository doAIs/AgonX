// 用户相关类型
export interface UserInfo {
  id: number
  username: string
  email: string
  avatar?: string
  created_at: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

// 聊天相关类型
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  images?: string[]
  timestamp: string
  agentName?: string
}

export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

// 知识库相关类型
export interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  created_at: string
}

export interface Document {
  id: string
  filename: string
  file_size: number
  chunk_count: number
  status: 'processing' | 'completed' | 'failed'
  created_at: string
}

export interface RetrievalConfig {
  chunk_size: number
  chunk_overlap: number
  top_k: number
  top_n: number
  similarity_threshold: number
  search_mode: 'vector' | 'keyword' | 'hybrid'
  rerank_enabled: boolean
}

// 智能体相关类型
export interface Agent {
  id: string
  name: string
  description: string
  type: 'researcher' | 'analyzer' | 'responder'
  enabled: boolean
}

export interface AgentTask {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  agents_involved: string[]
  created_at: string
  result?: string
}

// 记忆相关类型
export interface ShortTermMemory {
  id: string
  session_id: string
  content: string
  created_at: string
}

export interface LongTermMemory {
  id: string
  user_id: number
  content: string
  importance: number
  created_at: string
}

// 模型配置相关类型
export interface ModelConfig {
  id: number
  name: string
  provider: 'openai' | 'qwen' | 'deepseek' | 'glm'
  model_type: 'llm' | 'embedding'
  api_key: string
  base_url: string
  api_base?: string  // 兼容字段
  model?: string     // 模型标识符，如 gpt-4, qwen-max
  is_default: boolean
  temperature?: number
  top_p?: number
  max_tokens?: number
}

// API响应类型
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 分页类型
export interface PaginationParams {
  page: number
  page_size: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
