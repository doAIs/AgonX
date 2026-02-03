import request from './request'
import type { Message, ChatSession, ApiResponse, PaginatedResponse } from '@/types'

export const chatApi = {
  // 发送消息 (SSE流式响应)
  sendMessage(sessionId: string, content: string): EventSource {
    const token = localStorage.getItem('token')
    const url = `/api/v1/chat/message?session_id=${sessionId}&content=${encodeURIComponent(content)}`
    const eventSource = new EventSource(url)
    return eventSource
  },

  // 发送消息 (普通POST)
  sendMessagePost(data: { session_id: string; content: string }): Promise<ApiResponse<Message>> {
    return request.post('/chat/message', data)
  },

  // 获取会话列表
  getSessions(page: number = 1, pageSize: number = 20): Promise<ApiResponse<PaginatedResponse<ChatSession>>> {
    return request.get('/chat/sessions', { params: { page, page_size: pageSize } })
  },

  // 创建新会话
  createSession(title?: string): Promise<ApiResponse<ChatSession>> {
    return request.post('/chat/sessions', { title })
  },

  // 获取会话消息历史
  getHistory(sessionId: string): Promise<ApiResponse<Message[]>> {
    return request.get(`/chat/sessions/${sessionId}/messages`)
  },

  // 删除会话
  deleteSession(sessionId: string): Promise<ApiResponse<null>> {
    return request.delete(`/chat/sessions/${sessionId}`)
  },

  // 更新会话标题
  updateSession(sessionId: string, title: string): Promise<ApiResponse<ChatSession>> {
    return request.put(`/chat/sessions/${sessionId}`, { title })
  }
}
