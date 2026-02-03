import request from './request'
import type { LoginForm, RegisterForm, LoginResponse, UserInfo, ApiResponse } from '@/types'

export const authApi = {
  // 用户登录
  login(data: LoginForm): Promise<ApiResponse<LoginResponse>> {
    return request.post('/auth/login', data)
  },

  // 用户注册
  register(data: RegisterForm): Promise<ApiResponse<UserInfo>> {
    return request.post('/auth/register', data)
  },

  // 获取用户信息
  getUserInfo(): Promise<ApiResponse<UserInfo>> {
    return request.get('/auth/me')
  },

  // 刷新Token
  refreshToken(): Promise<ApiResponse<LoginResponse>> {
    return request.post('/auth/refresh')
  },

  // 退出登录
  logout(): Promise<ApiResponse<null>> {
    return request.post('/auth/logout')
  }
}
