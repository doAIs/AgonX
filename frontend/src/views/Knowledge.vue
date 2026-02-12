<template>
  <div class="knowledge-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>知识库管理</h2>
        <p>管理您的文档和知识库，支持多种检索模式</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建知识库
      </el-button>
    </div>

    <!-- 知识库列表 -->
    <div class="collections-grid">
      <div
        v-for="collection in collections"
        :key="collection.id"
        class="collection-card"
        @click="selectCollection(collection)"
      >
        <div class="card-header">
          <div class="card-icon">
            <el-icon :size="24"><Folder /></el-icon>
          </div>
          <el-dropdown trigger="click" @click.stop>
            <el-button :icon="More" text circle />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="editCollection(collection)">编辑</el-dropdown-item>
                <el-dropdown-item @click="deleteCollection(collection.id)" style="color: #ef4444">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <h3 class="card-title">{{ collection.name }}</h3>
        <p class="card-desc">{{ collection.description }}</p>
        <div class="card-stats">
          <span><el-icon><Document /></el-icon> {{ collection.document_count }} 文档</span>
          <span>{{ formatDate(collection.created_at) }}</span>
        </div>
      </div>

      <el-empty v-if="collections.length === 0" description="暂无知识库" />
    </div>

    <!-- 知识库详情抽屉 -->
    <el-drawer
      v-model="showDetail"
      :title="currentCollection?.name"
      direction="rtl"
      size="50%"
    >
      <div class="drawer-content" v-if="currentCollection">
        <!-- 文档上传 -->
        <div class="upload-section">
          <el-upload
            class="upload-area"
            drag
            :action="`/api/v1/knowledge/upload`"
            :headers="uploadHeaders"
            :data="{ collection_id: currentCollection.id }"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽文件到此处，或点击上传</div>
            <div class="upload-tip">支持 PDF、Word、TXT、Markdown 格式</div>
          </el-upload>
        </div>

        <!-- 检索配置 -->
        <div class="config-section">
          <h4>检索配置</h4>
          <el-form label-position="top">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="分块大小">
                  <el-input-number v-model="retrievalConfig.chunk_size" :min="100" :max="2000" :step="50" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="重叠大小">
                  <el-input-number v-model="retrievalConfig.chunk_overlap" :min="0" :max="200" :step="10" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="Top K (初步检索)">
                  <el-input-number v-model="retrievalConfig.top_k" :min="1" :max="50" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Top N (最终返回)">
                  <el-input-number v-model="retrievalConfig.top_n" :min="1" :max="20" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="相似度阈值">
              <el-slider v-model="retrievalConfig.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            <el-form-item label="检索模式">
              <el-radio-group v-model="retrievalConfig.search_mode">
                <el-radio-button value="vector">向量检索</el-radio-button>
                <el-radio-button value="keyword">关键词检索</el-radio-button>
                <el-radio-button value="hybrid">混合检索</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="重排序">
              <el-switch v-model="retrievalConfig.rerank_enabled" />
              <span class="config-tip">使用 BGE-Reranker 优化检索结果</span>
            </el-form-item>
            <el-button type="primary" @click="saveConfig">保存配置</el-button>
          </el-form>
        </div>

        <!-- 检索测试 -->
        <div class="test-section">
          <h4>检索测试</h4>
          <el-input
            v-model="testQuery"
            placeholder="输入查询内容进行测试"
            @keyup.enter="runTest"
          >
            <template #append>
              <el-button :icon="Search" @click="runTest" />
            </template>
          </el-input>
          <div class="test-results" v-if="testResults.length">
            <div class="result-item" v-for="(result, index) in testResults" :key="index">
              <div class="result-header">
                <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
                <span class="result-source">{{ result.source }}</span>
              </div>
              <div class="result-content">{{ result.content }}</div>
            </div>
          </div>
        </div>

        <!-- 文档列表 -->
        <div class="documents-section">
          <h4>文档列表</h4>
          <el-table :data="documents" style="width: 100%">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="chunk_count" label="分块数" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="danger" text size="small" @click="deleteDocument(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-drawer>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建知识库" width="500px">
      <el-form :model="newCollection" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="newCollection.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newCollection.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createCollection">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Folder,
  Document,
  More,
  UploadFilled,
  Search
} from '@element-plus/icons-vue'
import { knowledgeApi, type SearchResult } from '@/api/knowledge'
import type { KnowledgeBase, Document as DocType, RetrievalConfig } from '@/types'

const collections = ref<KnowledgeBase[]>([])
const currentCollection = ref<KnowledgeBase | null>(null)
const documents = ref<DocType[]>([])
const showDetail = ref(false)
const showCreateDialog = ref(false)
const testQuery = ref('')
const testResults = ref<SearchResult[]>([])

const newCollection = reactive({
  name: '',
  description: ''
})

const retrievalConfig = reactive<RetrievalConfig>({
  chunk_size: 512,
  chunk_overlap: 50,
  top_k: 10,
  top_n: 5,
  similarity_threshold: 0.7,
  search_mode: 'hybrid',
  rerank_enabled: true
})

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

async function selectCollection(collection: KnowledgeBase) {
  currentCollection.value = collection
  showDetail.value = true
  // 加载文档列表
  try {
    const res = await knowledgeApi.getDocuments(collection.id)
    documents.value = res.data.items
  } catch {
    documents.value = []
  }
  // 加载配置
  try {
    const configRes = await knowledgeApi.getConfig(collection.id)
    Object.assign(retrievalConfig, configRes.data)
  } catch {
    // 使用默认配置
  }
}

function editCollection(_collection: KnowledgeBase) {
  ElMessage.info('编辑功能开发中')
}

async function deleteCollection(id: string) {
  try {
    await knowledgeApi.deleteCollection(id)
    collections.value = collections.value.filter(c => c.id !== id)
    ElMessage.success('删除成功')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function createCollection() {
  if (!newCollection.name) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  try {
    const res = await knowledgeApi.createCollection(newCollection)
    collections.value.push(res.data)
    showCreateDialog.value = false
    newCollection.name = ''
    newCollection.description = ''
    ElMessage.success('创建成功')
  } catch {
    ElMessage.error('创建失败')
  }
}

function handleUploadSuccess(response: any) {
  console.log('上传成功:', response)
  ElMessage.success('文件上传成功，正在处理中...')
  if (currentCollection.value) {
    // 延迟刷新，等待后端处理完成
    setTimeout(() => {
      selectCollection(currentCollection.value!)
    }, 2000)
  }
}

function handleUploadError(error: any) {
  console.error('上传失败:', error)
  const errorMsg = error?.response?.data?.detail || error?.message || '上传失败，请检查后端日志'
  ElMessage.error(`上传失败: ${errorMsg}`)
}

async function saveConfig() {
  if (!currentCollection.value) return
  try {
    await knowledgeApi.updateConfig(currentCollection.value.id, retrievalConfig)
    ElMessage.success('配置保存成功')
  } catch {
    ElMessage.error('配置保存失败')
  }
}

async function runTest() {
  if (!testQuery.value || !currentCollection.value) return
  try {
    const res = await knowledgeApi.search({
      collection_id: currentCollection.value.id,
      query: testQuery.value,
      top_k: retrievalConfig.top_k,
      similarity_threshold: retrievalConfig.similarity_threshold,
      search_mode: retrievalConfig.search_mode
    })
    testResults.value = res.data
  } catch {
    ElMessage.error('检索测试失败')
  }
}

async function deleteDocument(id: string) {
  try {
    await knowledgeApi.deleteDocument(id)
    documents.value = documents.value.filter(d => d.id !== id)
    ElMessage.success('删除成功')
  } catch {
    ElMessage.error('删除失败')
  }
}

// 初始化加载知识库列表
async function fetchCollections() {
  try {
    const res = await knowledgeApi.getCollections()
    collections.value = res.data
  } catch (err) {
    console.error('获取知识库列表失败:', err)
    ElMessage.error('获取知识库列表失败')
  }
}

onMounted(() => {
  fetchCollections()
})
</script>

<style scoped>
.knowledge-page {
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

.collections-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.collection-card {
  background: rgba(22, 33, 62, 0.8);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
}

.collection-card:hover {
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-title {
  color: #e2e8f0;
  font-size: 18px;
  margin: 0 0 8px 0;
}

.card-desc {
  color: #a0aec0;
  font-size: 14px;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-stats {
  display: flex;
  justify-content: space-between;
  color: #718096;
  font-size: 12px;
}

.card-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.drawer-content {
  padding: 0 20px;
}

.upload-section,
.config-section,
.test-section,
.documents-section {
  margin-bottom: 32px;
}

.upload-section h4,
.config-section h4,
.test-section h4,
.documents-section h4 {
  color: #e2e8f0;
  margin: 0 0 16px 0;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(102, 126, 234, 0.3);
  border-radius: 12px;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #667eea;
}

.upload-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.upload-text {
  color: #e2e8f0;
  font-size: 16px;
  margin-bottom: 8px;
}

.upload-tip {
  color: #718096;
  font-size: 12px;
}

.config-tip {
  margin-left: 12px;
  color: #a0aec0;
  font-size: 12px;
}

.test-results {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  padding: 12px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-score {
  color: #10b981;
  font-size: 12px;
  font-weight: 500;
}

.result-source {
  color: #718096;
  font-size: 12px;
}

.result-content {
  color: #a0aec0;
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .collections-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
