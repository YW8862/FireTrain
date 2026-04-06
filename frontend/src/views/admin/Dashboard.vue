<template>
  <div class="dashboard">
    <h2 class="page-title">📊 系统概览</h2>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon user-icon">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_statistics?.total_users || 0 }}</div>
              <div class="stat-label">总用户数</div>
              <div class="stat-trend">
                今日新增: +{{ stats.user_statistics?.new_users_today || 0 }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon training-icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.training_statistics?.total_trainings || 0 }}</div>
              <div class="stat-label">总训练次数</div>
              <div class="stat-trend">
                今日训练: {{ stats.training_statistics?.trainings_today || 0 }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon score-icon">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.training_statistics?.average_score || 0 }}</div>
              <div class="stat-label">平均分数</div>
              <div class="stat-trend">满分 100 分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon video-icon">
              <el-icon :size="32"><VideoCamera /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.video_statistics?.pending || 0 }}</div>
              <div class="stat-label">待检测视频</div>
              <div class="stat-trend">
                已完成: {{ stats.video_statistics?.completed || 0 }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>用户角色分布</span>
            </div>
          </template>
          <div class="chart-placeholder">
            <div v-for="(count, role) in stats.user_statistics?.role_distribution" :key="role">
              <el-progress
                :percentage="calculatePercentage(count, totalUsers)"
                :format="() => `${getRoleLabel(role)}: ${count}`"
              />
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>训练类型分布</span>
            </div>
          </template>
          <div class="chart-placeholder">
            <div v-for="(count, type) in stats.training_statistics?.type_distribution" :key="type">
              <el-progress
                :percentage="calculatePercentage(count, totalTrainings)"
                :format="() => `${type}: ${count}`"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速操作 -->
    <el-card shadow="hover" class="quick-actions">
      <template #header>
        <div class="card-header">
          <span>⚡ 快速操作</span>
        </div>
      </template>
      <el-space wrap>
        <el-button type="primary" @click="$router.push('/admin/users')">
          <el-icon><User /></el-icon>
          用户管理
        </el-button>
        <el-button type="success" @click="$router.push('/admin/trainings')">
          <el-icon><Document /></el-icon>
          训练数据
        </el-button>
        <el-button type="info" @click="$router.push('/admin/logs')">
          <el-icon><List /></el-icon>
          操作日志
        </el-button>
      </el-space>
    </el-card>
    
    <!-- 刷新按钮 -->
    <div class="refresh-btn">
      <el-button @click="fetchStats" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboardStats } from '@/api/admin'
import { ElMessage } from 'element-plus'

const stats = ref({})
const loading = ref(false)

// 计算总数
const totalUsers = computed(() => {
  const dist = stats.value.user_statistics?.role_distribution || {}
  return Object.values(dist).reduce((sum, count) => sum + count, 0)
})

const totalTrainings = computed(() => {
  const dist = stats.value.training_statistics?.type_distribution || {}
  return Object.values(dist).reduce((sum, count) => sum + count, 0)
})

// 计算百分比
const calculatePercentage = (value, total) => {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

// 获取角色标签
const getRoleLabel = (role) => {
  const labelMap = {
    'root': 'Root',
    'admin': '管理员',
    'user': '普通用户',
    'student': '学员'
  }
  return labelMap[role] || role
}

// 获取统计数据
const fetchStats = async () => {
  loading.value = true
  try {
    const response = await getDashboardStats()
    stats.value = response
  } catch (error) {
    ElMessage.error('获取统计数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  height: 140px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.user-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.training-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.score-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.video-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
  color: #67c23a;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-placeholder {
  padding: 20px;
}

.quick-actions {
  margin-bottom: 20px;
}

.refresh-btn {
  text-align: right;
}
</style>
