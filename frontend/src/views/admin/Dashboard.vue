<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h2 class="page-title">系统概览</h2>
        <p class="page-subtitle">快速查看用户、训练、视频分析和后台常用入口。</p>
      </div>
      <el-button class="header-refresh" @click="fetchStats" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-card class="overview-hero" shadow="never">
      <div class="overview-hero-main">
        <div>
          <p class="overview-label">后台总览</p>
          <h3>训练系统运行状态</h3>
          <p class="overview-text">
            当前累计用户 {{ stats.user_statistics?.total_users || 0 }} 人，累计训练
            {{ stats.training_statistics?.total_trainings || 0 }} 次，待处理视频
            {{ stats.video_statistics?.pending || 0 }} 条。
          </p>
        </div>
        <div class="overview-tags">
          <span>用户管理</span>
          <span>训练数据</span>
          <span>视频分析</span>
        </div>
      </div>
    </el-card>
    
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
        <el-card shadow="hover" class="data-card">
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
        <el-card shadow="hover" class="data-card">
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
          <span>快速操作</span>
        </div>
      </template>
      <div class="quick-grid">
        <button type="button" class="quick-item" @click="$router.push('/admin/users')">
          <el-icon><User /></el-icon>
          <div>
            <strong>用户管理</strong>
            <span>查看账号、角色和状态</span>
          </div>
        </button>
        <button type="button" class="quick-item" @click="$router.push('/admin/trainings')">
          <el-icon><Document /></el-icon>
          <div>
            <strong>训练数据</strong>
            <span>检索训练记录和报告</span>
          </div>
        </button>
        <button type="button" class="quick-item" @click="$router.push('/admin/logs')">
          <el-icon><List /></el-icon>
          <div>
            <strong>操作日志</strong>
            <span>查看后台操作留痕</span>
          </div>
        </button>
      </div>
    </el-card>
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
  margin: 0;
  color: var(--ft-color-text-primary);
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
}

.overview-hero {
  margin-bottom: 20px;
  border-radius: 18px;
  border: 1px solid rgba(30, 64, 175, 0.12);
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.18), transparent 28%),
    linear-gradient(135deg, #16327d 0%, #1e40af 55%, #3159c7 100%);
  color: #fff;
}

.overview-hero :deep(.el-card__body) {
  padding: 24px 28px;
}

.overview-hero-main {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}

.overview-label {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}

.overview-hero h3 {
  margin: 0;
  font-size: 28px;
}

.overview-text {
  margin: 12px 0 0;
  max-width: 720px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.88);
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.overview-tags span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
  font-size: 13px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  height: 150px;
  border: 1px solid var(--ft-color-border);
  border-radius: 16px;
  overflow: hidden;
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
  background: rgba(30, 64, 175, 0.14);
  color: var(--ft-color-primary);
}

.training-icon {
  background: rgba(217, 33, 33, 0.12);
  color: var(--ft-color-danger);
}

.score-icon {
  background: rgba(16, 185, 129, 0.14);
  color: var(--ft-color-success);
}

.video-icon {
  background: rgba(217, 119, 6, 0.16);
  color: var(--ft-color-warning);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 30px;
  font-weight: bold;
  color: var(--ft-color-text-primary);
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
  color: var(--ft-color-text-secondary);
}

.charts-section {
  margin-bottom: 20px;
}

.data-card {
  border-radius: 16px;
}

.chart-placeholder {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.quick-actions {
  margin-bottom: 20px;
  border-radius: 16px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.quick-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--ft-color-border);
  border-radius: 14px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-2px);
  border-color: var(--ft-color-primary);
  box-shadow: var(--ft-shadow-sm);
}

.quick-item .el-icon {
  margin-top: 2px;
  font-size: 20px;
  color: var(--ft-color-primary);
}

.quick-item strong {
  display: block;
  font-size: 15px;
  color: var(--ft-color-text-primary);
}

.quick-item span {
  display: block;
  margin-top: 6px;
  color: var(--ft-color-text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 992px) {
  .overview-hero-main,
  .page-header {
    flex-direction: column;
  }

  .overview-tags {
    justify-content: flex-start;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
