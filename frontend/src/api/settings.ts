import request from './request'
import type { ModelConfig, ApiResponse } from '@/types'

export const settingsApi = {
  // 获取模型列表
  getModels(): Promise<ApiResponse<ModelConfig[]>> {
    return request.get('/settings/models')
  },

  // 添加模型配置
  addModel(data: Omit<ModelConfig, 'id'>): Promise<ApiResponse<ModelConfig>> {
    return request.post('/settings/models', data)
  },

  // 更新模型配置
  updateModel(id: number, data: Partial<ModelConfig>): Promise<ApiResponse<ModelConfig>> {
    return request.put(`/settings/models/${id}`, data)
  },

  // 删除模型配置
  deleteModel(id: number): Promise<ApiResponse<null>> {
    return request.delete(`/settings/models/${id}`)
  },

  // 设置默认模型
  setDefault(id: number): Promise<ApiResponse<ModelConfig>> {
    return request.post(`/settings/models/${id}/default`)
  },

  // 测试模型连接
  testConnection(data: { provider: string; api_key: string; base_url: string; model_type: string }): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return request.post('/settings/test', data)
  }
}
