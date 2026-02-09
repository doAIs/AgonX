<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>模型配置</h2>
        <p>配置 LLM 和 Embedding 模型，管理 API 密钥</p>
      </div>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加模型
      </el-button>
    </div>

    <!-- 模型选项卡 -->
    <el-tabs v-model="activeTab" class="model-tabs">
      <!-- LLM 模型 -->
      <el-tab-pane label="LLM 模型" name="llm">
        <div class="models-grid">
          <div
            v-for="model in llmModels"
            :key="model.id"
            class="model-card"
            :class="{ default: model.is_default }"
          >
            <div class="model-header">
              <div class="model-icon" :class="model.provider">
                <span>{{ getProviderIcon(model.provider) }}</span>
              </div>
              <div class="model-badge" v-if="model.is_default">默认</div>
            </div>
            <h4>{{ model.name }}</h4>
            <p class="model-provider">{{ getProviderName(model.provider) }}</p>
            <div class="model-params">
              <div class="param-item">
                <span>Temperature</span>
                <span>{{ model.temperature ?? 0.7 }}</span>
              </div>
              <div class="param-item">
                <span>Top P</span>
                <span>{{ model.top_p ?? 0.9 }}</span>
              </div>
            </div>
            <div class="model-actions">
              <el-button text type="primary" @click="editModel(model)">配置</el-button>
              <el-button text @click="testModel(model)">测试</el-button>
              <el-button
                v-if="!model.is_default"
                text
                type="success"
                @click="setDefaultModel(model)"
              >
                设为默认
              </el-button>
              <el-button text type="danger" @click="deleteModel(model.id)">删除</el-button>
            </div>
          </div>
          <el-empty v-if="llmModels.length === 0" description="暂无 LLM 模型配置" />
        </div>
      </el-tab-pane>

      <!-- Embedding 模型 -->
      <el-tab-pane label="Embedding 模型" name="embedding">
        <div class="models-grid">
          <div
            v-for="model in embeddingModels"
            :key="model.id"
            class="model-card"
            :class="{ default: model.is_default }"
          >
            <div class="model-header">
              <div class="model-icon embedding">
                <el-icon :size="24"><DataAnalysis /></el-icon>
              </div>
              <div class="model-badge" v-if="model.is_default">默认</div>
            </div>
            <h4>{{ model.name }}</h4>
            <p class="model-provider">{{ getProviderName(model.provider) }}</p>
            <div class="model-actions">
              <el-button text type="primary" @click="editModel(model)">配置</el-button>
              <el-button text @click="testModel(model)">测试</el-button>
              <el-button
                v-if="!model.is_default"
                text
                type="success"
                @click="setDefaultModel(model)"
              >
                设为默认
              </el-button>
              <el-button text type="danger" @click="deleteModel(model.id)">删除</el-button>
            </div>
          </div>
          <el-empty v-if="embeddingModels.length === 0" description="暂无 Embedding 模型配置" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑模型对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="isEditing ? '编辑模型' : '添加模型'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="modelForm" :rules="rules" ref="formRef" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模型类型" prop="model_type">
              <el-select v-model="modelForm.model_type" placeholder="选择模型类型" style="width: 100%">
                <el-option label="LLM 模型" value="llm" />
                <el-option label="Embedding 模型" value="embedding" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务商" prop="provider">
              <el-select v-model="modelForm.provider" placeholder="选择服务商" style="width: 100%">
                <el-option label="OpenAI" value="openai" />
                <el-option label="通义千问 (Qwen)" value="qwen" />
                <el-option label="DeepSeek" value="deepseek" />
                <el-option label="智谱 (GLM)" value="glm" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="模型名称" prop="name">
          <el-input v-model="modelForm.name" placeholder="例如: gpt-4, qwen-max, deepseek-chat" />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="modelForm.api_key"
            type="password"
            placeholder="输入 API Key"
            show-password
          />
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input v-model="modelForm.base_url" placeholder="可选，自定义 API 地址" />
          <div class="form-tip">
            <template v-if="modelForm.provider === 'qwen'">
              通义千问默认: https://dashscope.aliyuncs.com/compatible-mode/v1
            </template>
            <template v-else-if="modelForm.provider === 'deepseek'">
              DeepSeek 默认: https://api.deepseek.com
            </template>
            <template v-else-if="modelForm.provider === 'glm'">
              智谱默认: https://open.bigmodel.cn/api/paas/v4
            </template>
          </div>
        </el-form-item>

        <template v-if="modelForm.model_type === 'llm'">
          <el-divider>模型参数</el-divider>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="Temperature">
                <el-slider v-model="modelForm.temperature" :min="0" :max="2" :step="0.1" show-input />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Top P">
                <el-slider v-model="modelForm.top_p" :min="0" :max="1" :step="0.05" show-input />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="Max Tokens">
            <el-input-number v-model="modelForm.max_tokens" :min="100" :max="128000" :step="100" />
          </el-form-item>
        </template>

        <el-form-item>
          <el-button @click="testConnection" :loading="testing">
            <el-icon><Connection /></el-icon>
            测试连接
          </el-button>
          <span class="test-result" :class="testResult.status" v-if="testResult.message">
            {{ testResult.message }}
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, DataAnalysis, Connection } from '@element-plus/icons-vue'
import type { ModelConfig } from '@/types'

const activeTab = ref('llm')
const showAddDialog = ref(false)
const isEditing = ref(false)
const testing = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const testResult = reactive({ status: '', message: '' })

const models = ref<ModelConfig[]>([
  {
    id: 1,
    name: 'gpt-4',
    provider: 'openai',
    model_type: 'llm',
    api_key: 'sk-***',
    base_url: '',
    is_default: true,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 4096
  },
  {
    id: 2,
    name: 'qwen-max',
    provider: 'qwen',
    model_type: 'llm',
    api_key: 'sk-***',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    is_default: false,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 8192
  },
  {
    id: 3,
    name: 'bge-m3',
    provider: 'openai',
    model_type: 'embedding',
    api_key: 'sk-***',
    base_url: '',
    is_default: true
  }
])

const llmModels = computed(() => models.value.filter(m => m.model_type === 'llm'))
const embeddingModels = computed(() => models.value.filter(m => m.model_type === 'embedding'))

const modelForm = reactive<Partial<ModelConfig>>({
  name: '',
  provider: 'openai',
  model_type: 'llm',
  api_key: '',
  base_url: '',
  is_default: false,
  temperature: 0.7,
  top_p: 0.9,
  max_tokens: 4096
})

const rules: FormRules = {
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }]
}

function getProviderIcon(provider: string) {
  const icons: Record<string, string> = {
    openai: 'O',
    qwen: 'Q',
    deepseek: 'D',
    glm: 'G'
  }
  return icons[provider] || 'M'
}

function getProviderName(provider: string) {
  const names: Record<string, string> = {
    openai: 'OpenAI',
    qwen: '通义千问',
    deepseek: 'DeepSeek',
    glm: '智谱'
  }
  return names[provider] || provider
}

function editModel(model: ModelConfig) {
  isEditing.value = true
  Object.assign(modelForm, model)
  showAddDialog.value = true
}

async function testModel(model: ModelConfig) {
  ElMessage.info(`正在测试 ${model.name}...`)
  try {
    const response = await request.post('/settings/models/test', {
      provider: model.provider,
      api_base: model.api_base,
      api_key: model.api_key,
      model: model.model
    })
    if (response.data.status === 'success') {
      ElMessage.success(response.data.message)
    }
  } catch (error) {
    ElMessage.error('模型连接测试失败')
  }
}

async function setDefaultModel(model: ModelConfig) {
  models.value.forEach(m => {
    if (m.model_type === model.model_type) {
      m.is_default = m.id === model.id
    }
  })
  ElMessage.success(`已将 ${model.name} 设为默认模型`)
}

async function deleteModel(id: number) {
  models.value = models.value.filter(m => m.id !== id)
  ElMessage.success('删除成功')
}

async function testConnection() {
  testing.value = true
  testResult.status = ''
  testResult.message = ''
  
  try {
    // 模拟测试连接
    await new Promise(resolve => setTimeout(resolve, 1500))
    testResult.status = 'success'
    testResult.message = '连接成功!'
  } catch {
    testResult.status = 'error'
    testResult.message = '连接失败'
  } finally {
    testing.value = false
  }
}

async function saveModel() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        if (isEditing.value && modelForm.id) {
          // 更新
          const index = models.value.findIndex(m => m.id === modelForm.id)
          if (index !== -1) {
            models.value[index] = { ...modelForm } as ModelConfig
          }
        } else {
          // 新增
          models.value.push({
            ...modelForm,
            id: Date.now()
          } as ModelConfig)
        }
        showAddDialog.value = false
        ElMessage.success('保存成功')
      } finally {
        saving.value = false
      }
    }
  })
}

function resetForm() {
  isEditing.value = false
  testResult.status = ''
  testResult.message = ''
  Object.assign(modelForm, {
    name: '',
    provider: 'openai',
    model_type: 'llm',
    api_key: '',
    base_url: '',
    is_default: false,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 4096
  })
}
</script>

<style scoped>
.settings-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.model-tabs {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.model-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.model-tabs :deep(.el-tabs__nav-wrap::after) {
  background: rgba(102, 126, 234, 0.1);
}

.model-tabs :deep(.el-tabs__item) {
  color: #a0aec0;
}

.model-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.model-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.model-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s;
}

.model-card:hover {
  border-color: rgba(102, 126, 234, 0.3);
}

.model-card.default {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.05);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.model-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  color: white;
}

.model-icon.openai {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.model-icon.qwen {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.model-icon.deepseek {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.model-icon.glm {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.model-icon.embedding {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.model-badge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
}

.model-card h4 {
  color: #e2e8f0;
  font-size: 18px;
  margin: 0 0 4px 0;
}

.model-provider {
  color: #a0aec0;
  font-size: 14px;
  margin: 0 0 16px 0;
}

.model-params {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item span:first-child {
  color: #718096;
  font-size: 12px;
}

.param-item span:last-child {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
}

.model-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form-tip {
  margin-top: 8px;
  color: #718096;
  font-size: 12px;
}

.test-result {
  margin-left: 16px;
  font-size: 14px;
}

.test-result.success {
  color: #10b981;
}

.test-result.error {
  color: #ef4444;
}

@media (max-width: 1200px) {
  .models-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
