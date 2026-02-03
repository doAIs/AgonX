<template>
  <div class="chat-container">
    <!-- 会话列表侧边栏 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" class="new-chat-btn" @click="createNewSession">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
      </div>
      <div class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: chatStore.currentSession?.id === session.id }"
          @click="selectSession(session)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span class="session-title">{{ session.title || '新对话' }}</span>
          <el-button
            class="delete-btn"
            :icon="Delete"
            text
            size="small"
            @click.stop="deleteSession(session.id)"
          />
        </div>
        <el-empty v-if="chatStore.sessions.length === 0" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <!-- 对话主区域 -->
    <div class="chat-main">
      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="chatStore.messages.length === 0" class="welcome-screen">
          <div class="welcome-icon">
            <el-icon :size="64"><ChatDotRound /></el-icon>
          </div>
          <h2>欢迎使用 AgonX</h2>
          <p>多智能体协作平台，让AI为您服务</p>
          <div class="quick-prompts">
            <div class="prompt-card" v-for="prompt in quickPrompts" :key="prompt" @click="sendQuickPrompt(prompt)">
              {{ prompt }}
            </div>
          </div>
        </div>

        <div v-else class="messages-list">
          <div
            v-for="message in chatStore.messages"
            :key="message.id"
            class="message"
            :class="message.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="message.role === 'user'" :size="36" class="user-avatar">U</el-avatar>
              <div v-else class="ai-avatar">
                <el-icon :size="20"><Cpu /></el-icon>
              </div>
            </div>
            <div class="message-content">
              <div class="message-header" v-if="message.role === 'assistant'">
                <span class="agent-name">{{ message.agentName || 'AgonX' }}</span>
              </div>
              <div class="message-text" v-html="renderMarkdown(message.content)"></div>
              <!-- 图片渲染 -->
              <div v-if="message.images && message.images.length" class="message-images">
                <el-image
                  v-for="(img, index) in message.images"
                  :key="index"
                  :src="img"
                  :preview-src-list="message.images"
                  fit="cover"
                  class="message-image"
                />
              </div>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div v-if="chatStore.isStreaming" class="message assistant">
            <div class="message-avatar">
              <div class="ai-avatar streaming">
                <el-icon :size="20"><Cpu /></el-icon>
              </div>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 5 }"
            placeholder="输入消息，按 Enter 发送..."
            resize="none"
            class="message-input"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            class="send-btn"
            :disabled="!inputMessage.trim() || chatStore.isStreaming"
            @click="sendMessage"
          />
        </div>
        <div class="input-tips">
          <span>支持 Markdown 格式 | 多智能体协作模式</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import {
  Plus,
  Delete,
  ChatLineRound,
  ChatDotRound,
  Cpu,
  Promotion
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import type { Message } from '@/types'

const chatStore = useChatStore()
const messagesContainer = ref<HTMLElement | null>(null)
const inputMessage = ref('')

const quickPrompts = [
  '帮我分析一下项目架构',
  '查找相关技术文档',
  '总结会议内容',
  '生成代码示例'
]

onMounted(async () => {
  await chatStore.loadSessions()
  if (chatStore.sessions.length === 0) {
    await createNewSession()
  } else {
    const firstSession = chatStore.sessions[0]
    if (firstSession) {
      await chatStore.selectSession(firstSession)
    }
  }
})

watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

function renderMarkdown(content: string): string {
  try {
    return marked.parse(content) as string
  } catch {
    return content
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function createNewSession() {
  await chatStore.createSession()
}

async function selectSession(session: typeof chatStore.sessions[0]) {
  await chatStore.selectSession(session)
}

async function deleteSession(sessionId: string) {
  await chatStore.deleteSession(sessionId)
}

async function sendMessage() {
  const content = inputMessage.value.trim()
  if (!content || chatStore.isStreaming) return

  if (!chatStore.currentSession) {
    await createNewSession()
  }

  inputMessage.value = ''

  // 添加用户消息
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content,
    timestamp: new Date().toISOString()
  }
  chatStore.addMessage(userMessage)

  // 模拟AI响应（实际项目中会调用API）
  chatStore.isStreaming = true
  
  // 添加AI消息占位
  const aiMessage: Message = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString(),
    agentName: 'AgonX 智能体'
  }
  chatStore.addMessage(aiMessage)

  // 模拟流式响应
  const response = `收到您的问题："${content}"

让我为您分析一下...

**分析结果：**
1. 这是一个关于多智能体协作的问题
2. 系统正在调用相关智能体进行处理
3. 请稍候，正在整合信息...

目前这是一个演示响应，实际使用时会连接后端API进行处理。`

  let currentText = ''
  for (const char of response) {
    await new Promise(resolve => setTimeout(resolve, 20))
    currentText += char
    chatStore.updateLastMessage(currentText)
    scrollToBottom()
  }

  chatStore.isStreaming = false
}

function sendQuickPrompt(prompt: string) {
  inputMessage.value = prompt
  sendMessage()
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 112px);
  background: rgba(22, 33, 62, 0.5);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.chat-sidebar {
  width: 280px;
  background: rgba(22, 33, 62, 0.8);
  border-right: 1px solid rgba(102, 126, 234, 0.1);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.new-chat-btn {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  color: #a0aec0;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.session-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.session-item.active {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.delete-btn {
  opacity: 0;
  color: #ef4444;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.welcome-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #a0aec0;
}

.welcome-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 24px;
}

.welcome-screen h2 {
  color: #e2e8f0;
  margin-bottom: 8px;
}

.welcome-screen p {
  color: #718096;
  margin-bottom: 32px;
}

.quick-prompts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 500px;
}

.prompt-card {
  padding: 16px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.prompt-card:hover {
  background: rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.message {
  display: flex;
  gap: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.ai-avatar.streaming {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.message-content {
  max-width: 70%;
  background: rgba(255, 255, 255, 0.05);
  padding: 16px;
  border-radius: 16px;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message-header {
  margin-bottom: 8px;
}

.agent-name {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
}

.message-text {
  color: #e2e8f0;
  line-height: 1.6;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
}

.message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.message-images {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.message-image {
  width: 150px;
  height: 150px;
  border-radius: 8px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.input-container {
  padding: 16px 24px 24px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  color: #e2e8f0;
  padding: 12px 16px;
}

.message-input :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.input-tips {
  margin-top: 8px;
  font-size: 12px;
  color: #718096;
  text-align: center;
}
</style>
