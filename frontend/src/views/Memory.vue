<template>
  <div class="memory-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>记忆中心</h2>
        <p>管理短期记忆与长期记忆，提升对话质量</p>
      </div>
    </div>

    <!-- 记忆统计 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon short-term">
          <el-icon :size="24"><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ shortTermMemories.length }}</div>
          <div class="stat-title">短期记忆</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon long-term">
          <el-icon :size="24"><Collection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ longTermMemories.length }}</div>
          <div class="stat-title">长期记忆</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon sessions">
          <el-icon :size="24"><ChatLineSquare /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ sessionCount }}</div>
          <div class="stat-title">活跃会话</div>
        </div>
      </div>
    </div>

    <!-- 记忆选项卡 -->
    <el-tabs v-model="activeTab" class="memory-tabs">
      <!-- 短期记忆 -->
      <el-tab-pane label="短期记忆" name="short">
        <div class="tab-header">
          <p class="tab-desc">短期记忆存储当前会话的上下文，自动过期</p>
          <el-button type="danger" text @click="clearShortTermMemory">
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
        <div class="memory-list">
          <div class="memory-item" v-for="memory in shortTermMemories" :key="memory.id">
            <div class="memory-header">
              <span class="memory-session">会话: {{ memory.session_id.slice(0, 8) }}...</span>
              <span class="memory-time">{{ formatTime(memory.created_at) }}</span>
            </div>
            <div class="memory-content">{{ memory.content }}</div>
            <div class="memory-actions">
              <el-button text size="small" @click="promoteToLongTerm(memory)">
                <el-icon><TopRight /></el-icon>
                提升为长期记忆
              </el-button>
              <el-button text size="small" type="danger" @click="deleteMemory('short', memory.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          <el-empty v-if="shortTermMemories.length === 0" description="暂无短期记忆" />
        </div>
      </el-tab-pane>

      <!-- 长期记忆 -->
      <el-tab-pane label="长期记忆" name="long">
        <div class="tab-header">
          <p class="tab-desc">长期记忆永久保存，支持语义检索</p>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加记忆
          </el-button>
        </div>
        <div class="memory-list">
          <div class="memory-item" v-for="memory in longTermMemories" :key="memory.id">
            <div class="memory-header">
              <div class="importance-bar">
                <span>重要度:</span>
                <el-progress
                  :percentage="memory.importance * 100"
                  :stroke-width="6"
                  :color="getImportanceColor(memory.importance)"
                  style="width: 100px"
                />
              </div>
              <span class="memory-time">{{ formatTime(memory.created_at) }}</span>
            </div>
            <div class="memory-content">{{ memory.content }}</div>
            <div class="memory-actions">
              <el-button text size="small" @click="editMemory(memory)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button text size="small" type="danger" @click="deleteMemory('long', memory.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          <el-empty v-if="longTermMemories.length === 0" description="暂无长期记忆" />
        </div>
      </el-tab-pane>

      <!-- 记忆检索 -->
      <el-tab-pane label="记忆检索" name="search">
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="输入关键词或语句进行语义检索"
            size="large"
            @keyup.enter="searchMemory"
          >
            <template #append>
              <el-button :icon="Search" @click="searchMemory" />
            </template>
          </el-input>
          <div class="search-results" v-if="searchResults.length">
            <h4>检索结果 ({{ searchResults.length }} 条)</h4>
            <div class="result-item" v-for="(result, index) in searchResults" :key="index">
              <div class="result-header">
                <span class="result-score">相关度: {{ (result.score * 100).toFixed(1) }}%</span>
                <span class="result-type">{{ result.type === 'short' ? '短期' : '长期' }}</span>
              </div>
              <div class="result-content">{{ result.content }}</div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加记忆对话框 -->
    <el-dialog v-model="showAddDialog" title="添加长期记忆" width="500px">
      <el-form label-position="top">
        <el-form-item label="记忆内容" required>
          <el-input
            v-model="newMemory.content"
            type="textarea"
            :rows="4"
            placeholder="输入要记住的内容..."
          />
        </el-form-item>
        <el-form-item label="重要度">
          <el-slider v-model="newMemory.importance" :min="0" :max="1" :step="0.1" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addLongTermMemory">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Timer,
  Collection,
  ChatLineSquare,
  Delete,
  Plus,
  TopRight,
  Edit,
  Search
} from '@element-plus/icons-vue'
import type { ShortTermMemory, LongTermMemory } from '@/types'

const activeTab = ref('short')
const searchQuery = ref('')
const showAddDialog = ref(false)
const sessionCount = ref(5)

const shortTermMemories = ref<ShortTermMemory[]>([
  {
    id: '1',
    session_id: 'sess-abc12345',
    content: '用户询问了关于产品架构的问题，需要提供详细的技术方案',
    created_at: '2024-01-15T10:30:00Z'
  },
  {
    id: '2',
    session_id: 'sess-abc12345',
    content: '用户偏好使用中文回答，喜欢详细的解释和代码示例',
    created_at: '2024-01-15T10:25:00Z'
  }
])

const longTermMemories = ref<LongTermMemory[]>([
  {
    id: '1',
    user_id: 1,
    content: '用户是一名软件工程师，擅长Python和Vue.js开发',
    importance: 0.9,
    created_at: '2024-01-10T08:00:00Z'
  },
  {
    id: '2',
    user_id: 1,
    content: '用户正在开发一个多智能体协作平台项目',
    importance: 0.85,
    created_at: '2024-01-12T14:00:00Z'
  }
])

const searchResults = ref<Array<{ content: string; score: number; type: string }>>([])

const newMemory = reactive({
  content: '',
  importance: 0.5
})

function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

function getImportanceColor(importance: number) {
  if (importance >= 0.8) return '#10b981'
  if (importance >= 0.5) return '#f59e0b'
  return '#6b7280'
}

function promoteToLongTerm(memory: ShortTermMemory) {
  longTermMemories.value.push({
    id: Date.now().toString(),
    user_id: 1,
    content: memory.content,
    importance: 0.7,
    created_at: new Date().toISOString()
  })
  shortTermMemories.value = shortTermMemories.value.filter(m => m.id !== memory.id)
  ElMessage.success('已提升为长期记忆')
}

function deleteMemory(type: string, id: string) {
  if (type === 'short') {
    shortTermMemories.value = shortTermMemories.value.filter(m => m.id !== id)
  } else {
    longTermMemories.value = longTermMemories.value.filter(m => m.id !== id)
  }
  ElMessage.success('删除成功')
}

function clearShortTermMemory() {
  shortTermMemories.value = []
  ElMessage.success('短期记忆已清空')
}

function editMemory(memory: LongTermMemory) {
  ElMessage.info(`编辑记忆: ${memory.id}`)
}

function addLongTermMemory() {
  if (!newMemory.content) {
    ElMessage.warning('请输入记忆内容')
    return
  }
  longTermMemories.value.push({
    id: Date.now().toString(),
    user_id: 1,
    content: newMemory.content,
    importance: newMemory.importance,
    created_at: new Date().toISOString()
  })
  showAddDialog.value = false
  newMemory.content = ''
  newMemory.importance = 0.5
  ElMessage.success('添加成功')
}

function searchMemory() {
  if (!searchQuery.value) return
  // 模拟搜索结果
  searchResults.value = [
    {
      content: '用户是一名软件工程师，擅长Python和Vue.js开发',
      score: 0.92,
      type: 'long'
    },
    {
      content: '用户正在开发一个多智能体协作平台项目',
      score: 0.85,
      type: 'long'
    }
  ]
}
</script>

<style scoped>
.memory-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  color: #e2e8f0;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #a0aec0;
  margin: 0;
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

.stat-icon.short-term {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.long-term {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.stat-icon.sessions {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
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

.memory-tabs {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.memory-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.memory-tabs :deep(.el-tabs__nav-wrap::after) {
  background: rgba(102, 126, 234, 0.1);
}

.memory-tabs :deep(.el-tabs__item) {
  color: #a0aec0;
}

.memory-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.memory-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tab-desc {
  color: #a0aec0;
  font-size: 14px;
  margin: 0;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.memory-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  padding: 16px;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.memory-session {
  color: #667eea;
  font-size: 12px;
}

.memory-time {
  color: #718096;
  font-size: 12px;
}

.memory-content {
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.memory-actions {
  display: flex;
  gap: 8px;
}

.importance-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a0aec0;
  font-size: 12px;
}

.search-section {
  max-width: 800px;
}

.search-results {
  margin-top: 24px;
}

.search-results h4 {
  color: #e2e8f0;
  margin: 0 0 16px 0;
}

.result-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-score {
  color: #10b981;
  font-size: 12px;
}

.result-type {
  color: #667eea;
  font-size: 12px;
}

.result-content {
  color: #e2e8f0;
  font-size: 14px;
}
</style>
