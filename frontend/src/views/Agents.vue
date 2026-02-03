<template>
  <div class="agents-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>智能体管理</h2>
        <p>配置和管理多智能体协作任务</p>
      </div>
    </div>

    <!-- 智能体架构展示 -->
    <div class="architecture-section">
      <h3>多智能体协作架构</h3>
      <div class="workflow-diagram">
        <div class="workflow-node user-node">
          <el-icon :size="24"><User /></el-icon>
          <span>用户提问</span>
        </div>
        <div class="workflow-arrow">
          <el-icon><Right /></el-icon>
        </div>
        <div class="workflow-node orchestrator-node">
          <el-icon :size="24"><SetUp /></el-icon>
          <span>Orchestrator</span>
          <small>编排器</small>
        </div>
        <div class="workflow-branch">
          <div class="branch-line"></div>
          <div class="branch-nodes">
            <div class="workflow-node agent-node" v-for="agent in agents" :key="agent.id">
              <div class="agent-status" :class="{ active: agent.enabled }"></div>
              <el-icon :size="20"><component :is="getAgentIcon(agent.type)" /></el-icon>
              <span>{{ agent.name }}</span>
              <small>{{ agent.description }}</small>
            </div>
          </div>
        </div>
        <div class="workflow-arrow">
          <el-icon><Right /></el-icon>
        </div>
        <div class="workflow-node result-node">
          <el-icon :size="24"><ChatDotRound /></el-icon>
          <span>最终响应</span>
        </div>
      </div>
    </div>

    <!-- 智能体列表 -->
    <div class="agents-section">
      <h3>智能体配置</h3>
      <div class="agents-grid">
        <div class="agent-card" v-for="agent in agents" :key="agent.id">
          <div class="agent-header">
            <div class="agent-icon" :class="agent.type">
              <el-icon :size="28"><component :is="getAgentIcon(agent.type)" /></el-icon>
            </div>
            <el-switch v-model="agent.enabled" @change="toggleAgent(agent)" />
          </div>
          <h4>{{ agent.name }}</h4>
          <p>{{ agent.description }}</p>
          <div class="agent-type">
            <el-tag :type="getAgentTagType(agent.type)" size="small">
              {{ getAgentTypeText(agent.type) }}
            </el-tag>
          </div>
          <div class="agent-actions">
            <el-button text type="primary" @click="editAgent(agent)">配置</el-button>
            <el-button text @click="testAgent(agent)">测试</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务历史 -->
    <div class="tasks-section">
      <h3>任务历史</h3>
      <el-table :data="taskHistory" style="width: 100%">
        <el-table-column prop="id" label="任务ID" width="200" />
        <el-table-column prop="agents_involved" label="参与智能体">
          <template #default="{ row }">
            <el-tag v-for="agent in row.agents_involved" :key="agent" size="small" class="agent-tag">
              {{ agent }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)" size="small">
              {{ getTaskStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewTaskDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 智能体配置对话框 -->
    <el-dialog v-model="showConfigDialog" :title="`配置 ${currentAgent?.name}`" width="600px">
      <el-form v-if="currentAgent" label-position="top">
        <el-form-item label="智能体名称">
          <el-input v-model="currentAgent.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="currentAgent.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input
            v-model="agentSystemPrompt"
            type="textarea"
            :rows="6"
            placeholder="定义智能体的行为和能力..."
          />
        </el-form-item>
        <el-form-item label="可用工具">
          <el-checkbox-group v-model="agentTools">
            <el-checkbox value="knowledge_search">知识库检索</el-checkbox>
            <el-checkbox value="image_search">图片搜索</el-checkbox>
            <el-checkbox value="web_search">网络搜索</el-checkbox>
            <el-checkbox value="code_executor">代码执行</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAgentConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  User,
  Right,
  SetUp,
  Search,
  DataAnalysis,
  ChatDotRound,
  Cpu
} from '@element-plus/icons-vue'
import type { Agent, AgentTask } from '@/types'

const agents = ref<Agent[]>([
  {
    id: '1',
    name: 'Researcher',
    description: '负责从知识库检索信息、查找相关图片和文档',
    type: 'researcher',
    enabled: true
  },
  {
    id: '2',
    name: 'Analyzer',
    description: '负责信息整合、逻辑推理和数据分析',
    type: 'analyzer',
    enabled: true
  },
  {
    id: '3',
    name: 'Responder',
    description: '负责生成最终答案、格式化输出内容',
    type: 'responder',
    enabled: true
  }
])

const taskHistory = ref<AgentTask[]>([
  {
    id: 'task-001',
    status: 'completed',
    agents_involved: ['Researcher', 'Analyzer', 'Responder'],
    created_at: '2024-01-15T10:30:00Z',
    result: '任务完成'
  },
  {
    id: 'task-002',
    status: 'completed',
    agents_involved: ['Researcher', 'Responder'],
    created_at: '2024-01-15T09:15:00Z',
    result: '任务完成'
  }
])

const showConfigDialog = ref(false)
const currentAgent = ref<Agent | null>(null)
const agentSystemPrompt = ref('')
const agentTools = ref<string[]>(['knowledge_search'])

function getAgentIcon(type: string) {
  const icons: Record<string, typeof Search> = {
    researcher: Search,
    analyzer: DataAnalysis,
    responder: ChatDotRound
  }
  return icons[type] || Cpu
}

function getAgentTagType(type: string) {
  const types: Record<string, string> = {
    researcher: 'primary',
    analyzer: 'warning',
    responder: 'success'
  }
  return types[type] || 'info'
}

function getAgentTypeText(type: string) {
  const texts: Record<string, string> = {
    researcher: '研究员',
    analyzer: '分析师',
    responder: '响应者'
  }
  return texts[type] || type
}

function getTaskStatusType(status: string) {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function getTaskStatusText(status: string) {
  const texts: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

function toggleAgent(agent: Agent) {
  ElMessage.success(`${agent.name} 已${agent.enabled ? '启用' : '禁用'}`)
}

function editAgent(agent: Agent) {
  currentAgent.value = { ...agent }
  showConfigDialog.value = true
}

function testAgent(agent: Agent) {
  ElMessage.info(`测试 ${agent.name} 智能体...`)
}

function saveAgentConfig() {
  if (!currentAgent.value) return
  const index = agents.value.findIndex(a => a.id === currentAgent.value!.id)
  if (index !== -1) {
    agents.value[index] = currentAgent.value
  }
  showConfigDialog.value = false
  ElMessage.success('配置保存成功')
}

function viewTaskDetail(task: AgentTask) {
  ElMessage.info(`查看任务详情: ${task.id}`)
}
</script>

<style scoped>
.agents-page {
  max-width: 1400px;
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

.architecture-section,
.agents-section,
.tasks-section {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.architecture-section h3,
.agents-section h3,
.tasks-section h3 {
  color: #e2e8f0;
  font-size: 18px;
  margin: 0 0 24px 0;
}

.workflow-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
}

.workflow-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  color: #e2e8f0;
  min-width: 120px;
}

.workflow-node span {
  font-size: 14px;
  font-weight: 500;
}

.workflow-node small {
  font-size: 12px;
  color: #a0aec0;
}

.user-node {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
  border-color: rgba(16, 185, 129, 0.3);
}

.orchestrator-node {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-color: rgba(102, 126, 234, 0.3);
}

.result-node {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%);
  border-color: rgba(245, 158, 11, 0.3);
}

.workflow-arrow {
  color: #667eea;
  font-size: 24px;
}

.workflow-branch {
  position: relative;
  display: flex;
  align-items: center;
}

.branch-nodes {
  display: flex;
  gap: 16px;
}

.agent-node {
  position: relative;
  min-width: 100px;
}

.agent-status {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #718096;
}

.agent-status.active {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.agent-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s;
}

.agent-card:hover {
  border-color: rgba(102, 126, 234, 0.3);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.agent-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.agent-icon.researcher {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.agent-icon.analyzer {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.agent-icon.responder {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.agent-card h4 {
  color: #e2e8f0;
  font-size: 18px;
  margin: 0 0 8px 0;
}

.agent-card p {
  color: #a0aec0;
  font-size: 14px;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.agent-type {
  margin-bottom: 16px;
}

.agent-actions {
  display: flex;
  gap: 8px;
}

.agent-tag {
  margin-right: 8px;
}

@media (max-width: 1200px) {
  .agents-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
