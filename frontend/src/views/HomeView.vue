<template>
  <div class="home-container">
    <div class="main-content">
      <el-card class="welcome-card">
        <div class="welcome-content">
          <div class="welcome-icon">
            <el-icon :size="120"><video-camera /></el-icon>
          </div>
          <h2 class="welcome-title">欢迎使用消防技能训练系统</h2>
          <p class="welcome-subtitle">智能评估 · 规范操作 · 安全训练</p>
          
          <div class="features">
            <el-row :gutter="40">
              <el-col :span="8">
                <div class="feature-item">
                  <el-icon :size="48" color="#409EFF"><video-camera /></el-icon>
                  <h3>AI 智能评估</h3>
                  <p>基于计算机视觉技术，实时分析操作动作</p>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="feature-item">
                  <el-icon :size="48" color="#67C23A"><document-checked /></el-icon>
                  <h3>标准化流程</h3>
                  <p>严格按照消防操作规范，培养正确习惯</p>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="feature-item">
                  <el-icon :size="48" color="#E6A23C"><data-line /></el-icon>
                  <h3>数据统计分析</h3>
                  <p>记录训练历史，可视化展示进步轨迹</p>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large" 
              @click="goToTraining"
              class="start-btn"
            >
              <el-icon><video-play /></el-icon>
              去训练
            </el-button>
            
            <el-button 
              size="large" 
              @click="viewHistory"
              class="secondary-btn"
            >
              <el-icon><document /></el-icon>
              查看历史记录
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  VideoCamera, 
  DocumentChecked, 
  DataLine,
  VideoPlay,
  Document,
  ArrowDown,
  UserFilled
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 用户信息
const userName = computed(() => {
  return userStore.user?.username || '用户'
})

// 跳转到训练页面
const goToTraining = () => {
  router.push('/training')
}

// 查看历史记录
const viewHistory = () => {
  router.push('/history')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

/* 主内容区 */
.main-content {
  padding: 60px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  width: 100%;
}

.welcome-card {
  max-width: 1000px;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
}

.welcome-content {
  padding: 60px 40px;
  text-align: center;
}

.welcome-icon {
  margin-bottom: 30px;
  color: #E6A23C;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.welcome-title {
  font-size: 36px;
  color: #303133;
  margin: 0 0 15px 0;
  font-weight: 600;
}

.welcome-subtitle {
  font-size: 18px;
  color: #909399;
  margin: 0 0 50px 0;
}

.features {
  margin-bottom: 50px;
}

.feature-item {
  padding: 30px 20px;
  text-align: center;
}

.feature-item h3 {
  margin: 15px 0 10px 0;
  font-size: 20px;
  color: #303133;
}

.feature-item p {
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.start-btn {
  padding: 15px 40px;
  font-size: 18px;
  height: auto;
}

.secondary-btn {
  padding: 15px 40px;
  font-size: 18px;
  height: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    padding: 40px 20px;
  }

  .welcome-title {
    font-size: 28px;
  }

  .welcome-subtitle {
    font-size: 16px;
  }

  .feature-item h3 {
    font-size: 18px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .start-btn,
  .secondary-btn {
    width: 100%;
  }
}
</style>
