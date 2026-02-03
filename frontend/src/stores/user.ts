import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserInfo, LoginForm } from '@/types'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(form: LoginForm) {
    const res = await authApi.login(form)
    token.value = res.data.access_token
    localStorage.setItem('token', res.data.access_token)
    return res
  }

  async function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  async function getUserInfo() {
    if (!token.value) return null
    const res = await authApi.getUserInfo()
    userInfo.value = res.data
    return res.data
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    logout,
    getUserInfo
  }
})
