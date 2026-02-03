import request from './request'
import type { KnowledgeBase, Document, RetrievalConfig, ApiResponse, PaginatedResponse } from '@/types'

export interface SearchResult {
  id: string
  content: string
  score: number
  metadata: Record<string, unknown>
  source: string
}

export const knowledgeApi = {
  // 获取知识库列表
  getCollections(): Promise<ApiResponse<KnowledgeBase[]>> {
    return request.get('/knowledge/collections')
  },

  // 创建知识库
  createCollection(data: { name: string; description: string }): Promise<ApiResponse<KnowledgeBase>> {
    return request.post('/knowledge/collections', data)
  },

  // 删除知识库
  deleteCollection(id: string): Promise<ApiResponse<null>> {
    return request.delete(`/knowledge/collections/${id}`)
  },

  // 上传文档
  uploadDocument(collectionId: string, file: File): Promise<ApiResponse<Document>> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection_id', collectionId)
    return request.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取文档列表
  getDocuments(collectionId: string, page: number = 1, pageSize: number = 20): Promise<ApiResponse<PaginatedResponse<Document>>> {
    return request.get(`/knowledge/collections/${collectionId}/documents`, {
      params: { page, page_size: pageSize }
    })
  },

  // 删除文档
  deleteDocument(documentId: string): Promise<ApiResponse<null>> {
    return request.delete(`/knowledge/documents/${documentId}`)
  },

  // 向量检索
  search(data: {
    collection_id: string
    query: string
    top_k?: number
    similarity_threshold?: number
    search_mode?: string
  }): Promise<ApiResponse<SearchResult[]>> {
    return request.post('/knowledge/search', data)
  },

  // 获取检索配置
  getConfig(collectionId: string): Promise<ApiResponse<RetrievalConfig>> {
    return request.get(`/knowledge/collections/${collectionId}/config`)
  },

  // 更新检索配置
  updateConfig(collectionId: string, config: Partial<RetrievalConfig>): Promise<ApiResponse<RetrievalConfig>> {
    return request.put(`/knowledge/collections/${collectionId}/config`, config)
  }
}
