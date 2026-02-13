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
          <div class="section-header">
            <h4>📄 文档上传</h4>
            <el-tag type="info" size="small">自动向量化并保存原文件</el-tag>
          </div>
          <el-upload
            class="upload-area"
            drag
            :action="`/api/v1/knowledge/upload`"
            :headers="uploadHeaders"
            :data="{ collection_id: currentCollection.id }"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="handleBeforeUpload"
            accept=".pdf,.doc,.docx,.txt,.md"
            multiple
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽文件到此处，或点击上传</div>
            <div class="upload-tip">支持 PDF、Word、TXT、Markdown 格式，上传后自动向量化</div>
          </el-upload>
          <div class="upload-notice">
            <el-icon><InfoFilled /></el-icon>
            <span>文档上传后会自动进行向量化处理，原文件安全存储于MinIO，可随时下载</span>
          </div>
        </div>

        <!-- 检索配置 -->
        <div class="config-section">
          <div class="section-header">
            <h4>⚙️ 检索配置</h4>
            <el-button type="primary" size="small" @click="saveConfig" :loading="saving">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
          </div>
          <el-form label-position="top" class="config-form">
            <el-card shadow="never" class="config-card">
              <template #header>
                <span>分块设置</span>
              </template>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="分块大小">
                    <el-input-number v-model="retrievalConfig.chunk_size" :min="100" :max="2000" :step="50" style="width: 100%" />
                    <div class="form-tip">每个文本块的字符数</div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="重叠大小">
                    <el-input-number v-model="retrievalConfig.chunk_overlap" :min="0" :max="200" :step="10" style="width: 100%" />
                    <div class="form-tip">相邻分块重叠的字符数</div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>
            
            <el-card shadow="never" class="config-card">
              <template #header>
                <span>检索参数</span>
              </template>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="Top K (初步检索)">
                    <el-input-number v-model="retrievalConfig.top_k" :min="1" :max="50" style="width: 100%" />
                    <div class="form-tip">从向量库检索的数量</div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Top N (最终返回)">
                    <el-input-number v-model="retrievalConfig.top_n" :min="1" :max="20" style="width: 100%" />
                    <div class="form-tip">重排序后返回的数量</div>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="相似度阈值">
                <el-slider v-model="retrievalConfig.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
                <div class="form-tip">低于此值的结果将被过滤</div>
              </el-form-item>
            </el-card>
            
            <el-card shadow="never" class="config-card">
              <template #header>
                <span>检索模式</span>
              </template>
              <el-form-item label="选择模式">
                <el-radio-group v-model="retrievalConfig.search_mode" size="large">
                  <el-radio-button value="vector">
                    <el-icon><Histogram /></el-icon>
                    向量检索
                  </el-radio-button>
                  <el-radio-button value="keyword">
                    <el-icon><Search /></el-icon>
                    关键词检索
                  </el-radio-button>
                  <el-radio-button value="hybrid">
                    <el-icon><Connection /></el-icon>
                    混合检索
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-switch v-model="retrievalConfig.rerank_enabled" size="large" />
                <span class="config-tip">启用 BGE-Reranker 重排序（提高精准度）</span>
              </el-form-item>
            </el-card>
          </el-form>
        </div>

        <!-- 检索测试 -->
        <div class="test-section">
          <div class="section-header">
            <h4>🔍 检索测试</h4>
            <div style="display: flex; align-items: center; gap: 12px;">
              <el-switch v-model="useEnhancedSearch" active-text="富媒体模式" inactive-text="基础模式" size="large" />
              <el-tag v-if="testResults.length" type="success" size="small">找到 {{ testResults.length }} 条结果</el-tag>
            </div>
          </div>
          <el-input
            v-model="testQuery"
            placeholder="输入查询内容进行测试（例如：AgonX是什么？）"
            size="large"
            @keyup.enter="runTest"
            :loading="testing"
          >
            <template #append>
              <el-button :icon="Search" @click="runTest" :loading="testing">检索</el-button>
            </template>
          </el-input>
          
          <!-- 基础结果展示 -->
          <div class="test-results" v-if="testResults.length && !useEnhancedSearch">
            <div class="result-item" v-for="(result, index) in testResults" :key="index">
              <div class="result-header">
                <div class="result-rank">#{{ index + 1 }}</div>
                <span class="result-score">
                  <el-icon><Odometer /></el-icon>
                  {{ (result.score * 100).toFixed(1) }}%
                </span>
                <span class="result-source">
                  <el-icon><Document /></el-icon>
                  {{ result.source.split('/').pop() }}
                </span>
              </div>
              <div class="result-content">{{ result.content }}</div>
            </div>
          </div>
          
          <!-- 增强结果展示 -->
          <div class="enhanced-results" v-if="enhancedResults.length && useEnhancedSearch">
            <div class="enhanced-result-item" v-for="(result, index) in enhancedResults" :key="result.id">
              <div class="result-header">
                <div class="result-rank">#{{ index + 1 }}</div>
                <span class="result-score">
                  <el-icon><Odometer /></el-icon>
                  {{ (result.score * 100).toFixed(1) }}%
                </span>
                <span class="result-source" v-if="result.document">
                  <el-icon><Document /></el-icon>
                  {{ result.document.filename }}
                </span>
                <span class="page-badge" v-if="result.page_info">
                  📝 第 {{ result.page_info.page_number }} 页
                </span>
              </div>
              
              <!-- 主内容 -->
              <div class="result-content">{{ result.content }}</div>
              
              <!-- 上下文 -->
              <div class="context-section" v-if="result.context.before.length || result.context.after.length">
                <el-divider content-position="left">📄 上下文</el-divider>
                <div class="context-text" v-if="result.context.before.length">
                  <strong>上文：</strong> {{ result.context.before.join(' ... ') }}
                </div>
                <div class="context-text" v-if="result.context.after.length">
                  <strong>下文：</strong> {{ result.context.after.join(' ... ') }}
                </div>
              </div>
              
              <!-- 页面预览 -->
              <div class="page-preview" v-if="result.page_info?.thumbnail_url">
                <el-divider content-position="left">🖼️ 页面预览</el-divider>
                <el-image
                  :src="result.page_info.thumbnail_url"
                  fit="contain"
                  style="max-width: 200px; border-radius: 8px; cursor: pointer;"
                  :preview-src-list="[result.page_info.page_image_url || result.page_info.thumbnail_url]"
                />
              </div>
              
              <!-- 关联图片 -->
              <div class="related-images" v-if="result.related_images.length">
                <el-divider content-position="left">🖼️ 关联图片 ({{ result.related_images.length }})</el-divider>
                <div class="images-grid">
                  <div v-for="(img, idx) in result.related_images" :key="idx" class="image-item">
                    <el-image
                      :src="img.thumbnail_url || img.url"
                      fit="cover"
                      style="width: 120px; height: 120px; border-radius: 8px;"
                      :preview-src-list="[img.url]"
                    />
                    <div class="image-ocr" v-if="img.ocr_text">
                      <el-tooltip :content="img.ocr_text" placement="top">
                        <el-tag size="small" type="info">🔍 OCR识别</el-tag>
                      </el-tooltip>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 操作按钮 -->
              <div class="result-actions">
                <el-button size="small" type="primary" text v-if="result.document" @click="downloadDocumentById(result.document.id, result.document.filename)">
                  <el-icon><Download /></el-icon>
                  下载原文档
                </el-button>
              </div>
            </div>
          </div>
          
          <el-empty v-if="testQuery && !testing && testResults.length === 0 && enhancedResults.length === 0" description="暂无检索结果" />
        </div>

        <!-- 文档列表 -->
        <div class="documents-section">
          <div class="section-header">
            <h4>📁 文档列表</h4>
            <el-tag type="info" size="small">{{ documents.length }} 个文档</el-tag>
          </div>
          <el-table :data="documents" style="width: 100%" :empty-text="'请上传文档'">
            <el-table-column prop="filename" label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="filename-cell">
                  <el-icon :size="16"><Document /></el-icon>
                  <span>{{ row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="分块数" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" v-if="row.chunk_count">{{ row.chunk_count }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button type="primary" text size="small" @click="downloadDocument(row)" :icon="Download">
                    下载
                  </el-button>
                  <el-button type="danger" text size="small" @click="deleteDocument(row.id)" :icon="Delete">
                    删除
                  </el-button>
                </el-button-group>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Folder,
  Document,
  More,
  UploadFilled,
  Search,
  InfoFilled,
  Check,
  Histogram,
  Connection,
  Odometer,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { knowledgeApi, type SearchResult, type EnhancedSearchResult } from '@/api/knowledge'
import type { KnowledgeBase, Document as DocType, RetrievalConfig } from '@/types'

const collections = ref<KnowledgeBase[]>([])
const currentCollection = ref<KnowledgeBase | null>(null)
const documents = ref<DocType[]>([])
const showDetail = ref(false)
const showCreateDialog = ref(false)
const testQuery = ref('')
const testResults = ref<SearchResult[]>([])
const enhancedResults = ref<EnhancedSearchResult[]>([])
const useEnhancedSearch = ref(true)  // 默认使用增强模式
const saving = ref(false)
const testing = ref(false)

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

// 监听抽屉打开状态，自动加载文档列表
watch(showDetail, (newVal) => {
  if (newVal && currentCollection.value) {
    // 抽屉打开且有选中的知识库时，加载文档
    loadDocuments(currentCollection.value.id)
  }
})

// 加载文档列表的独立函数
async function loadDocuments(kbId: string) {
  try {
    console.log('正在加载文档列表...')
    const res = await knowledgeApi.getDocuments(kbId)
    documents.value = res.data.items
    console.log(`加载了 ${res.data.items.length} 个文档`)
  } catch (error) {
    console.error('加载文档失败:', error)
    documents.value = []
  }
}

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
  await loadDocuments(collection.id)
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

function handleBeforeUpload() {
  ElMessage.info('开始上传文档...')
  return true
}

function handleUploadSuccess(response: any) {
  console.log('上传成功:', response)
  ElMessage.success({
    message: '文件上传成功！正在进行向量化处理...',
    duration: 3000
  })
  // 立即刷新文档列表
  if (currentCollection.value) {
    loadDocuments(currentCollection.value.id)
    // 3秒后再次刷新，获取处理后的状态
    setTimeout(() => {
      if (currentCollection.value) {
        loadDocuments(currentCollection.value.id)
      }
    }, 3000)
  }
}

function handleUploadError(error: any) {
  console.error('上传失败:', error)
  let errorMsg = '上传失败'
  
  if (error?.response?.data?.detail) {
    errorMsg = error.response.data.detail
  } else if (error?.response?.status) {
    errorMsg = `服务器错误 (${error.response.status})`
  } else if (error?.message) {
    errorMsg = error.message
  }
  
  ElMessage.error(`上传失败: ${errorMsg}`)
  console.log('错误详情:', {
    status: error?.response?.status,
    statusText: error?.response?.statusText,
    data: error?.response?.data,
    message: error?.message
  })
}

async function saveConfig() {
  if (!currentCollection.value) return
  saving.value = true
  try {
    await knowledgeApi.updateConfig(currentCollection.value.id, retrievalConfig)
    ElMessage.success('✅ 检索配置已保存')
  } catch {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

async function runTest() {
  if (!testQuery.value || !currentCollection.value) {
    ElMessage.warning('请输入查询内容')
    return
  }
  testing.value = true
  try {
    if (useEnhancedSearch.value) {
      // 使用增强检索
      const res = await knowledgeApi.enhancedSearch({
        collection_id: currentCollection.value.id,
        query: testQuery.value,
        top_k: retrievalConfig.top_k,
        similarity_threshold: retrievalConfig.similarity_threshold,
        search_mode: retrievalConfig.search_mode
      })
      enhancedResults.value = res.data
      testResults.value = []  // 清空基础结果
      if (res.data.length === 0) {
        ElMessage.warning('未找到相关结果，请尝试降低相似度阈值或更改查询内容')
      } else {
        ElMessage.success(`✅ 找到 ${res.data.length} 条相关结果（富媒体模式）`)
      }
    } else {
      // 使用基础检索
      const res = await knowledgeApi.search({
        collection_id: currentCollection.value.id,
        query: testQuery.value,
        top_k: retrievalConfig.top_k,
        similarity_threshold: retrievalConfig.similarity_threshold,
        search_mode: retrievalConfig.search_mode
      })
      testResults.value = res.data
      enhancedResults.value = []  // 清空增强结果
      if (res.data.length === 0) {
        ElMessage.warning('未找到相关结果，请尝试降低相似度阈值或更改查询内容')
      } else {
        ElMessage.success(`✅ 找到 ${res.data.length} 条相关结果`)
      }
    }
  } catch (error: any) {
    ElMessage.error(`检索失败: ${error.response?.data?.detail || error.message}`)
    testResults.value = []
    enhancedResults.value = []
  } finally {
    testing.value = false
  }
}

async function downloadDocumentById(docId: string, filename: string) {
  try {
    const token = localStorage.getItem('token')
    const url = `/api/v1/knowledge/documents/${docId}/download`
    
    ElMessage.info('正在下载...')
    
    // 使用 fetch 获取文件
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('下载失败')
    }
    
    // 转换为 Blob
    const blob = await response.blob()
    
    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename  // 设置文件名
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    
    ElMessage.success('下载完成！')
  } catch (error: any) {
    console.error('下载错误:', error)
    ElMessage.error('下载失败，请重试')
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function downloadDocument(doc: DocType) {
  try {
    const token = localStorage.getItem('token')
    const url = `/api/v1/knowledge/documents/${doc.id}/download`
    
    ElMessage.info('正在下载...')
    
    // 使用 fetch 获取文件
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('下载失败')
    }
    
    // 转换为 Blob
    const blob = await response.blob()
    
    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = doc.filename  // 设置文件名
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    
    ElMessage.success('下载完成！')
  } catch (error: any) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败，请重试')
  }
}

async function deleteDocument(id: string) {
  try {
    await ElMessageBox.confirm('确认删除该文档吗？删除后将同时删除向量数据，不可恢复！', '警告', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeApi.deleteDocument(id)
    documents.value = documents.value.filter(d => d.id !== id)
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.upload-section,
.config-section,
.test-section,
.documents-section {
  margin-bottom: 32px;
}

.upload-notice {
  margin-top: 12px;
  padding: 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  color: #93c5fd;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
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

/* 标签深色主题 */
:deep(.el-tag--info) {
  background: rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.25);
  color: #a5b4fc;
}

/* 文档列表深色主题 */
.documents-section :deep(.el-table) {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.6);
  --el-table-row-hover-bg-color: rgba(102, 126, 234, 0.08);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.documents-section :deep(.el-table__header) {
  background: rgba(15, 23, 42, 0.6);
}

.documents-section :deep(.el-table__header-wrapper th) {
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  font-weight: 600;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.documents-section :deep(.el-table__body-wrapper td) {
  background: transparent;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(102, 126, 234, 0.05);
}

.documents-section :deep(.el-table__empty-block) {
  background: rgba(15, 23, 42, 0.3);
}

.documents-section :deep(.el-table__empty-text) {
  color: #64748b;
}

/* 文件名单元格 */
.filename-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
}

.filename-cell .el-icon {
  color: #667eea;
}

.config-tip {
  margin-left: 12px;
  color: #a0aec0;
  font-size: 12px;
}

/* 检索配置卡片深色主题 */
.config-card {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  margin-bottom: 16px;
}

.config-card :deep(.el-card__header) {
  background: rgba(15, 23, 42, 0.5);
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  padding: 12px 20px;
}

.config-card :deep(.el-card__header span) {
  color: #e2e8f0;
  font-weight: 600;
  font-size: 14px;
}

.config-card :deep(.el-card__body) {
  background: transparent;
  padding: 20px;
}

/* 表单标签深色主题 */
.config-form :deep(.el-form-item__label) {
  color: #94a3b8;
  font-weight: 500;
}

/* 输入框深色主题 */
.config-form :deep(.el-input-number) {
  background: rgba(15, 23, 42, 0.4);
}

.config-form :deep(.el-input-number .el-input__inner) {
  background: rgba(15, 23, 42, 0.4);
  border-color: rgba(102, 126, 234, 0.2);
  color: #e2e8f0;
}

.config-form :deep(.el-input-number:hover .el-input__inner) {
  border-color: rgba(102, 126, 234, 0.4);
}

/* 滑块深色主题 */
.config-form :deep(.el-slider__runway) {
  background: rgba(102, 126, 234, 0.2);
}

.config-form :deep(.el-slider__bar) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.config-form :deep(.el-slider__button) {
  background: #667eea;
  border-color: #667eea;
}

.config-form :deep(.el-slider__input) {
  background: rgba(15, 23, 42, 0.4);
}

.config-form :deep(.el-slider__input .el-input__inner) {
  background: rgba(15, 23, 42, 0.4);
  border-color: rgba(102, 126, 234, 0.2);
  color: #e2e8f0;
}

/* 单选按钮深色主题 */
.config-form :deep(.el-radio-button__inner) {
  background: rgba(15, 23, 42, 0.4);
  border-color: rgba(102, 126, 234, 0.2);
  color: #94a3b8;
}

.config-form :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  box-shadow: -1px 0 0 0 #667eea;
}

/* 开关深色主题 */
.config-form :deep(.el-switch__label) {
  color: #94a3b8;
}

.config-form :deep(.el-switch__label.is-active) {
  color: #e2e8f0;
}

/* 表单提示文字 */
.form-tip {
  color: #64748b;
  font-size: 12px;
  margin-top: 4px;
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
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s;
}

.result-item:hover {
  border-color: rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.04);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.result-rank {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.result-score {
  color: #10b981;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-source {
  color: #718096;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.result-content {
  color: #a0aec0;
  font-size: 14px;
  line-height: 1.6;
}

/* 增强结果样式 */
.enhanced-results {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.enhanced-result-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s;
}

.enhanced-result-item:hover {
  border-color: rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.page-badge {
  padding: 4px 12px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 6px;
  color: #93c5fd;
  font-size: 12px;
  font-weight: 500;
}

.context-section {
  margin-top: 16px;
  padding: 12px;
  background: rgba(59, 130, 246, 0.05);
  border-left: 3px solid rgba(59, 130, 246, 0.5);
  border-radius: 4px;
}

.context-text {
  color: #a0aec0;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.context-text:last-child {
  margin-bottom: 0;
}

.context-text strong {
  color: #93c5fd;
  margin-right: 8px;
}

.page-preview {
  margin-top: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.related-images {
  margin-top: 16px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.image-item {
  position: relative;
}

.image-ocr {
  position: absolute;
  bottom: 4px;
  left: 4px;
  right: 4px;
  display: flex;
  justify-content: center;
}

.result-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
  display: flex;
  gap: 8px;
}

@media (max-width: 1200px) {
  .collections-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
