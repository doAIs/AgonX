<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.title">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-title">{{ stat.title }}</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="section">
      <h3 class="section-title">快捷操作</h3>
      <div class="quick-actions">
        <div class="action-card" @click="$router.push('/chat')">
          <el-icon :size="32" color="#667eea"><ChatDotRound /></el-icon>
          <span>开始对话</span>
        </div>
        <div class="action-card" @click="$router.push('/knowledge')">
          <el-icon :size="32" color="#10b981"><FolderAdd /></el-icon>
          <span>上传文档</span>
        </div>
        <div class="action-card" @click="$router.push('/agents')">
          <el-icon :size="32" color="#f59e0b"><UserFilled /></el-icon>
          <span>配置智能体</span>
        </div>
        <div class="action-card" @click="$router.push('/settings')">
          <el-icon :size="32" color="#8b5cf6"><Setting /></el-icon>
          <span>模型设置</span>
        </div>
      </div>
    </div>

    <!-- 最近对话 -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">最近对话</h3>
        <el-button type="primary" text @click="$router.push('/chat')">查看全部</el-button>
      </div>
      <div class="recent-chats">
        <div class="chat-item" v-for="chat in recentChats" :key="chat.id">
          <div class="chat-icon">
            <el-icon :size="20"><ChatLineRound /></el-icon>
          </div>
          <div class="chat-content">
            <div class="chat-title">{{ chat.title }}</div>
            <div class="chat-time">{{ chat.time }}</div>
          </div>
          <el-button type="primary" text size="small">继续</el-button>
        </div>
        <el-empty v-if="recentChats.length === 0" description="暂无对话记录" />
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="section">
      <h3 class="section-title">系统状态</h3>
      <div class="status-grid">
        <div class="status-item" v-for="item in systemStatus" :key="item.name">
          <div class="status-indicator" :class="item.status"></div>
          <span class="status-name">{{ item.name }}</span>
          <span class="status-text">{{ item.text }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  ChatDotRound,
  ChatLineRound,
  FolderAdd,
  UserFilled,
  Setting,
  Document,
  Cpu,
  Connection
} from '@element-plus/icons-vue'

const stats = ref([
  { title: '总对话数', value: '128', icon: ChatDotRound, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { title: '知识库文档', value: '56', icon: Document, gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' },
  { title: '智能体任务', value: '89', icon: Cpu, gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' },
  { title: '记忆条目', value: '1.2k', icon: Connection, gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' }
])

const recentChats = ref([
  { id: '1', title: '关于产品设计的讨论', time: '2小时前' },
  { id: '2', title: '技术架构分析', time: '5小时前' },
  { id: '3', title: '项目进度汇报', time: '1天前' }
])

const systemStatus = ref([
  { name: 'LLM服务', status: 'online', text: '运行中' },
  { name: '向量数据库', status: 'online', text: '运行中' },
  { name: '对象存储', status: 'online', text: '运行中' },
  { name: '缓存服务', status: 'online', text: '运行中' }
])
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-4px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #e2e8f0;
}

.stat-title {
  font-size: 14px;
  color: #a0aec0;
  margin-top: 4px;
}

.section {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 20px 0;
}

.section-header .section-title {
  margin: 0;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-card:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-4px);
}

.action-card span {
  color: #a0aec0;
  font-size: 14px;
}

.recent-chats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  transition: all 0.3s;
}

.chat-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.chat-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.chat-content {
  flex: 1;
}

.chat-title {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
}

.chat-time {
  color: #718096;
  font-size: 12px;
  margin-top: 4px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.online {
  background: #10b981;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

.status-indicator.offline {
  background: #ef4444;
}

.status-name {
  color: #e2e8f0;
  font-size: 14px;
  flex: 1;
}

.status-text {
  color: #10b981;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .stats-grid,
  .quick-actions,
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
