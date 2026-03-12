<template>
  <div class="training-container">
    <el-card class="training-card">
      <template #header>
        <div class="card-header">
          <h1>🔥 训练开始</h1>
          <div>
            <el-tag v-if="currentTraining" :type="getStatusType(currentTraining.status)">
              {{ getStatusText(currentTraining.status) }}
            </el-tag>
            <el-button v-if="currentTraining?.status === 'done'" type="primary" size="small" @click="resetTraining">
              新的训练
            </el-button>
          </div>
        </div>
      </template>

      <!-- 未开始训练 -->
      <div v-if="!currentTraining">
        <el-alert
          title="训练说明"
          type="info"
          :closable="false"
          show-icon
          class="mb-4"
        >
          <p>请按照标准流程完成灭火器操作训练：</p>
          <ol>
            <li>准备阶段：做好个人防护，确认逃生路线</li>
            <li>提起灭火器：用腿部力量提起灭火器</li>
            <li>拔保险销：握住拉环用力拔出</li>
            <li>握喷管：双手稳固握持喷管</li>
            <li>瞄准火源：对准火焰根部，保持 2-3 米距离</li>
            <li>压把手：均匀用力下压，左右扫射</li>
          </ol>
        </el-alert>

        <el-form :model="trainingForm" label-width="120px">
          <el-form-item label="训练类型">
            <el-select v-model="trainingForm.training_type" placeholder="请选择训练类型">
              <el-option label="灭火器操作" value="fire_extinguisher" />
              <el-option label="其他训练" value="other" />
            </el-select>
          </el-form-item>

          <el-form-item label="预计时长（秒）">
            <el-input-number v-model="trainingForm.duration_seconds" :min="60" :max="300" :step="10" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleStartTraining" :loading="starting" size="large">
              开始训练
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 训练中 -->
      <div v-else>
        <!-- 摄像头画面 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :span="16">
            <div class="video-container">
              <video ref="videoRef" autoplay playsinline class="video-element"></video>
              <div v-if="!cameraStarted" class="video-overlay">
                <el-button type="primary" @click="startCamera" size="large">
                  <el-icon><VideoCamera /></el-icon>
                  开启摄像头
                </el-button>
              </div>
            </div>
          </el-col>

          <el-col :span="8">
            <!-- 实时步骤状态 -->
            <el-card class="steps-card">
              <template #header>
                <span>📋 操作步骤</span>
              </template>
              <el-timeline>
                <el-timeline-item
                  v-for="(step, index) in steps"
                  :key="index"
                  :timestamp="step.name"
                  placement="top"
                  :icon="getStepIcon(step.status)"
                  :color="getStepColor(step.status)"
                >
                  {{ step.name }}
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>
        </el-row>

        <!-- 控制按钮 -->
        <div class="control-buttons">
          <el-button 
            type="success" 
            @click="handleCompleteTraining" 
            :loading="completing" 
            :disabled="currentTraining?.status === 'done'"
            size="large"
          >
            完成训练
          </el-button>
          <el-button type="warning" @click="handlePause" :disabled="!cameraStarted">
            暂停
          </el-button>
          <el-button type="danger" @click="handleCancel" :disabled="!cameraStarted">
            取消
          </el-button>
        </div>

        <!-- 倒计时 -->
        <div v-if="countdown > 0" class="countdown">
          <el-progress type="circle" :percentage="100" :format="() => countdown + 's'" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import { startTraining, completeTraining } from '@/api/training'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 状态
const starting = ref(false)
const completing = ref(false)
const cameraStarted = ref(false)
const countdown = ref(0)
const videoRef = ref(null)
let stream = null
let countdownTimer = null

// 训练表单
const trainingForm = reactive({
  training_type: 'fire_extinguisher',
  duration_seconds: 120
})

// 当前训练
const currentTraining = ref(null)

// 步骤状态
const steps = reactive([
  { name: '准备阶段', status: 'pending' },
  { name: '提灭火器', status: 'pending' },
  { name: '拔保险销', status: 'pending' },
  { name: '握喷管', status: 'pending' },
  { name: '瞄准火源', status: 'pending' },
  { name: '压把手', status: 'pending' }
])

// 开启摄像头
const startCamera = async () => {
  try {
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    })
    
    stream = mediaStream
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      cameraStarted.value = true
      ElMessage.success('摄像头已开启')
      
      // TODO: 这里可以添加 AI 分析逻辑
      // 实时分析视频帧，更新步骤状态
    }
  } catch (error) {
    console.error('无法访问摄像头:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  }
}

// 停止摄像头
const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  cameraStarted.value = false
}

// 开始训练
const handleStartTraining = async () => {
  starting.value = true
  try {
    const res = await startTraining(trainingForm)
    currentTraining.value = res
    ElMessage.success('训练已开始')
    
    // 自动开启摄像头
    setTimeout(() => startCamera(), 500)
  } catch (error) {
    console.error('启动训练失败:', error)
    ElMessage.error(error.response?.data?.detail || '启动训练失败')
  } finally {
    starting.value = false
  }
}

// 完成训练
const handleCompleteTraining = async () => {
  // 检查当前状态
  if (currentTraining.value?.status === 'done') {
    ElMessage.warning('该训练已完成，请勿重复提交')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要完成训练吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    completing.value = true
    const res = await completeTraining(currentTraining.value.training_id)
    
    ElMessage.success('训练已完成')
    stopCamera()
    
    // 更新当前训练状态
    currentTraining.value = res
    
    // 跳转到报告页面
    router.push(`/report/${res.training_id}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('完成训练失败:', error)
      // 如果是状态错误，给出更友好的提示
      if (error.response?.data?.detail?.includes('当前状态')) {
        ElMessage.error('训练状态异常，请刷新页面后重试')
      } else {
        ElMessage.error(error.response?.data?.detail || '完成训练失败，请稍后重试')
      }
    }
  } finally {
    completing.value = false
  }
}

// 暂停训练
const handlePause = () => {
  ElMessage.info('训练已暂停')
  // TODO: 实现暂停逻辑
}

// 取消训练
const handleCancel = () => {
  ElMessageBox.confirm('确定要取消训练吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    stopCamera()
    currentTraining.value = null
    ElMessage.success('已取消训练')
  }).catch(() => {})
}

// 获取步骤图标
const getStepIcon = (status) => {
  switch (status) {
    case 'done':
      return 'Check'
    case 'doing':
      return 'Loading'
    case 'error':
      return 'Close'
    default:
      return 'Clock'
  }
}

// 获取步骤颜色
const getStepColor = (status) => {
  switch (status) {
    case 'done':
      return '#67C23A'
    case 'doing':
      return '#409EFF'
    case 'error':
      return '#F56C6C'
    default:
      return '#909399'
  }
}

// 获取状态标签类型
const getStatusType = (status) => {
  const map = {
    created: 'info',
    processing: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const map = {
    created: '未开始',
    processing: '进行中',
    done: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

// 重置训练状态
const resetTraining = () => {
  stopCamera()
  currentTraining.value = null
  ElMessage.success('已准备就绪，可以开始新的训练')
}

// 组件卸载时清理
onUnmounted(() => {
  stopCamera()
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.training-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.training-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mb-4 {
  margin-bottom: 1rem;
}

.video-container {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16/9;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
}

.steps-card {
  height: 100%;
}

.control-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.countdown {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 999;
}
</style>
