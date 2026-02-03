import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '@/api/chat'
import type { Message, ChatSession } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)

  async function loadSessions() {
    const res = await chatApi.getSessions()
    sessions.value = res.data.items
  }

  async function createSession(title?: string) {
    const res = await chatApi.createSession(title)
    sessions.value.unshift(res.data)
    currentSession.value = res.data
    messages.value = []
    return res.data
  }

  async function selectSession(session: ChatSession) {
    currentSession.value = session
    const res = await chatApi.getHistory(session.id)
    messages.value = res.data
  }

  async function deleteSession(sessionId: string) {
    await chatApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSession.value?.id === sessionId) {
      currentSession.value = null
      messages.value = []
    }
  }

  function addMessage(message: Message) {
    messages.value.push(message)
  }

  function updateLastMessage(content: string) {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.content = content
      }
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    sessions,
    currentSession,
    messages,
    isLoading,
    isStreaming,
    loadSessions,
    createSession,
    selectSession,
    deleteSession,
    addMessage,
    updateLastMessage,
    clearMessages
  }
})
