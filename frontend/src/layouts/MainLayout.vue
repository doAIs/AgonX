<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-container">
        <div class="logo">
          <span class="logo-icon">A</span>
          <span v-show="!isCollapse" class="logo-text">AgonX</span>
        </div>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        class="sidebar-menu"
        router
        background-color="transparent"
        text-color="#a0aec0"
        active-text-color="#667eea"
      >
        <el-menu-item 
          v-for="item in menuItems" 
          :key="item.path" 
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button 
          :icon="isCollapse ? Expand : Fold" 
          text 
          @click="toggleCollapse"
          class="collapse-btn"
        />
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="36" class="user-avatar">
                {{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() || 'U' }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.username || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Odometer, 
  ChatDotRound, 
  Collection, 
  UserFilled, 
  Memo, 
  Setting,
  Tools,
  Fold,
  Expand,
  ArrowDown
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/chat', title: '智能对话', icon: ChatDotRound },
  { path: '/knowledge', title: '知识库', icon: Collection },
  { path: '/agents', title: '智能体', icon: UserFilled },
  { path: '/tools', title: 'MCP工具', icon: Tools },
  { path: '/memory', title: '记忆中心', icon: Memo },
  { path: '/settings', title: '模型配置', icon: Setting }
]

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => {
  const item = menuItems.find(m => m.path === route.path)
  return item?.title || ''
})

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

async function handleCommand(command: string) {
  if (command === 'logout') {
    await userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
}

.sidebar {
  background: rgba(22, 33, 62, 0.95);
  border-right: 1px solid rgba(102, 126, 234, 0.1);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  backdrop-filter: blur(10px);
}

.logo-container {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  color: white;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-menu {
  flex: 1;
  border: none;
  padding: 10px;
}

.sidebar-menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin-bottom: 4px;
  height: 48px;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(102, 126, 234, 0.1) !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%) !important;
  color: #667eea !important;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.collapse-btn {
  width: 100%;
  color: #a0aec0;
}

.main-container {
  display: flex;
  flex-direction: column;
}

.header {
  height: 64px;
  background: rgba(22, 33, 62, 0.8);
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  backdrop-filter: blur(10px);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #a0aec0;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.username {
  font-size: 14px;
}

.main-content {
  padding: 24px;
  background: transparent;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
