<template>
  <div class="tools-container">
    <el-card class="header-card">
      <h2>MCP 工具管理</h2>
      <p class="subtitle">管理和测试 Model Context Protocol 工具</p>
    </el-card>

    <!-- 工具列表 -->
    <el-row :gutter="20">
      <el-col :span="12" v-for="tool in tools" :key="tool.name">
        <el-card class="tool-card" shadow="hover">
          <template #header>
            <div class="tool-header">
              <el-icon class="tool-icon"><Tools /></el-icon>
              <span class="tool-name">{{ tool.name }}</span>
              <el-tag :type="getToolTypeTag(tool.name)" size="small">
                {{ getToolCategory(tool.name) }}
              </el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="tool-description">{{ tool.description }}</p>
            
            <div class="tool-params">
              <h4>参数</h4>
              <el-table :data="tool.schema.parameters" size="small" stripe>
                <el-table-column prop="name" label="参数名" width="120" />
                <el-table-column prop="type" label="类型" width="80" />
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="required" label="必需" width="60">
                  <template #default="{ row }">
                    <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                      {{ row.required ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="tool-actions">
              <el-button type="primary" size="small" @click="openTestDialog(tool)">
                <el-icon><Operation /></el-icon>
                测试工具
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试工具"
      width="600px"
      class="test-dialog"
    >
      <el-form v-if="currentTool" :model="testForm" label-width="100px">
        <el-form-item
          v-for="param in currentTool.schema.parameters"
          :key="param.name"
          :label="param.name"
          :required="param.required"
        >
          <el-input
            v-model="testForm.arguments[param.name]"
            :placeholder="param.description"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="testDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="testing" @click="testTool">
          执行测试
        </el-button>
      </template>
    </el-dialog>

    <!-- 结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="执行结果"
      width="700px"
      class="result-dialog"
    >
      <el-alert
        :type="testResult?.success ? 'success' : 'error'"
        :title="testResult?.success ? '执行成功' : '执行失败'"
        :closable="false"
        show-icon
      />
      <div class="result-content">
        <pre>{{ JSON.stringify(testResult?.result || testResult?.error, null, 2) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Tools, Operation } from '@element-plus/icons-vue'
import request from '@/api/request'

interface Tool {
  name: string
  description: string
  schema: {
    parameters: Array<{
      name: string
      type: string
      description: string
      required: boolean
      default?: any
    }>
  }
}

const tools = ref<Tool[]>([])
const testDialogVisible = ref(false)
const resultDialogVisible = ref(false)
const currentTool = ref<Tool | null>(null)
const testing = ref(false)
const testResult = ref<any>(null)

const testForm = ref({
  arguments: {} as Record<string, any>
})

onMounted(async () => {
  await loadTools()
})

async function loadTools() {
  try {
    const response = await request.get('/mcp/tools')
    tools.value = response.data.tools
  } catch (error) {
    ElMessage.error('加载工具列表失败')
  }
}

function getToolCategory(name: string): string {
  if (name.includes('weather')) return '天气'
  if (name.includes('order')) return '订单'
  return '其他'
}

function getToolTypeTag(name: string): string {
  if (name.includes('weather')) return 'success'
  if (name.includes('order')) return 'warning'
  return 'info'
}

function openTestDialog(tool: Tool) {
  currentTool.value = tool
  testForm.value.arguments = {}
  
  // 设置默认值
  tool.schema.parameters.forEach(param => {
    if (param.default !== undefined) {
      testForm.value.arguments[param.name] = param.default
    }
  })
  
  testDialogVisible.value = true
}

async function testTool() {
  if (!currentTool.value) return
  
  testing.value = true
  try {
    const response = await request.post('/mcp/execute', {
      tool_name: currentTool.value.name,
      arguments: testForm.value.arguments
    })
    
    testResult.value = response.data
    testDialogVisible.value = false
    resultDialogVisible.value = true
    
    if (response.data.success) {
      ElMessage.success('工具执行成功')
    }
  } catch (error) {
    ElMessage.error('工具执行失败')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.tools-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.header-card h2 {
  margin: 0 0 8px 0;
  color: #e2e8f0;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  color: #a0aec0;
  font-size: 14px;
}

.tool-card {
  margin-bottom: 20px;
  background: rgba(22, 33, 62, 0.6);
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s;
}

.tool-card:hover {
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-icon {
  font-size: 20px;
  color: #667eea;
}

.tool-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
}

.tool-content {
  color: #cbd5e0;
}

.tool-description {
  margin-bottom: 16px;
  line-height: 1.6;
  color: #a0aec0;
}

.tool-params {
  margin-bottom: 16px;
}

.tool-params h4 {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 14px;
}

.tool-actions {
  display: flex;
  justify-content: flex-end;
}

.test-dialog :deep(.el-dialog) {
  background: rgba(22, 33, 62, 0.95);
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.test-dialog :deep(.el-dialog__title) {
  color: #e2e8f0;
}

.result-dialog :deep(.el-dialog) {
  background: rgba(22, 33, 62, 0.95);
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.result-content {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.result-content pre {
  margin: 0;
  color: #e2e8f0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>
