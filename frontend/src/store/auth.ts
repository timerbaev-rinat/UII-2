// Pinia-стор аутентификации.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/endpoints'
import { clearTokens, getAccessToken, setTokens } from '@/api/client'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!getAccessToken())
  const hasRole = (codes: string[]): boolean => {
    if (!user.value) return false
    return user.value.roles.some((r) => codes.includes(r.code))
  }
  const isAdmin = computed(() => hasRole(['ADMIN']))
  const isZavhoz = computed(() => hasRole(['ADMIN', 'ZAVHOZ']))

  async function fetchMe(): Promise<User | null> {
    if (!getAccessToken()) return null
    try {
      user.value = await authApi.me()
      return user.value
    } catch {
      clearTokens()
      user.value = null
      return null
    }
  }

  async function login(login: string, password: string): Promise<void> {
    loading.value = true
    try {
      const tokens = await authApi.login({ login, password })
      setTokens(tokens)
      await fetchMe()
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    clearTokens()
    user.value = null
  }

  return {
    user,
    loading,
    initialized,
    isAuthenticated,
    isAdmin,
    isZavhoz,
    hasRole,
    login,
    logout,
    fetchMe,
  }
})