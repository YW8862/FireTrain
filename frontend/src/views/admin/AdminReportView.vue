<template>
  <div class="admin-report-container">
    <div class="admin-report-content">
      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/admin/trainings' }">训练数据</el-breadcrumb-item>
        <el-breadcrumb-item>训练报告</el-breadcrumb-item>
      </el-breadcrumb>

      <div v-loading="loading" class="report-wrapper">
        <!-- 训练记录信息卡片 -->
        <el-card shadow="hover" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">📋 训练记录详情</span>
              <el-tag type="info" size="small">ID: {{ trainingInfo?.id }}</el-tag>
            </div>
          </template>
          <el-descriptions :column="3" border size="large">
            <el-descriptions-item label="用户名" label-align="right">
              <el-tag type="primary" effect="dark">{{ trainingInfo?.username }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="训练类型" label-align="right">
              {{ getTrainingTypeLabel(trainingInfo?.training_type) }}
            </el-descriptions-item>
            <el-descriptions-item label="状态" label-align="right">
              <el-tag :type="getStatusType(trainingInfo?.status)" effect="dark">
                {{ getStatusLabel(trainingInfo?.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="开始时间" label-align="right">
              {{ formatDateTime(trainingInfo?.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间" label-align="right">
              {{ trainingInfo?.completed_at ? formatDateTime(trainingInfo?.completed_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="训练时长" label-align="right">
              <el-tag v-if="trainingInfo?.duration_seconds" type="warning">
                {{ trainingInfo.duration_seconds }}秒
              </el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 评分概览卡片 -->
        <el-row :gutter="20" class="score-cards">
          <el-col :span="6">
            <el-card shadow="hover" class="score-card total-score">
              <div class="score-value">{{ reportData.total_score }}</div>
              <div class="score-label">总分</div>
              <el-progress
                :percentage="reportData.total_score"
                :color="getScoreColor(reportData.total_score)"
                :stroke-width="8"
                :show-text="false"
              />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="score-card">
              <div class="score-value" :style="{ color: getDimensionColor(reportData.dimension_scores?.action_completeness?.score ?? reportData.total_score) }">
                {{ reportData.dimension_scores?.action_completeness?.score ?? reportData.total_score }}
              </div>
              <div class="score-label">动作完整性</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="score-card">
              <div class="score-value" :style="{ color: getDimensionColor(reportData.dimension_scores?.pose_standardization?.score ?? reportData.total_score * 0.95) }">
                {{ reportData.dimension_scores?.pose_standardization?.score ?? Math.round(reportData.total_score * 0.95) }}
              </div>
              <div class="score-label">姿态规范性</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="score-card">
              <div class="score-value" :style="{ color: getDimensionColor(reportData.dimension_scores?.timeliness?.score ?? reportData.total_score * 0.9) }">
                {{ reportData.dimension_scores?.timeliness?.score ?? Math.round(reportData.total_score * 0.9) }}
              </div>
              <div class="score-label">操作时效性</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 详细分析区域 -->
        <el-row :gutter="20">
          <!-- 左侧：雷达图 -->
          <el-col :span="10">
            <el-card shadow="hover" class="chart-card">
              <template #header>
                <span class="card-title">📊 能力维度分析</span>
              </template>
              <div ref="radarChartRef" class="radar-chart"></div>
            </el-card>
          </el-col>

          <!-- 右侧：步骤评分 -->
          <el-col :span="14">
            <el-card shadow="hover" class="steps-card">
              <template #header>
                <span class="card-title">📝 步骤评分详情</span>
              </template>
              <div class="steps-list">
                <div v-for="(step, index) in reportData.step_scores" :key="index" class="step-item">
                  <div class="step-header">
                    <span class="step-name">
                      <el-tag size="small" type="info">{{ index + 1 }}</el-tag>
                      {{ step.step_name }}
                    </span>
                    <el-tag :type="getScoreTagType(step.score)" effect="dark">
                      {{ step.score }}分
                    </el-tag>
                  </div>
                  <el-progress
                    :percentage="step.score"
                    :color="getStepColor(step.score)"
                    :stroke-width="6"
                  />
                  <p v-if="step.feedback" class="step-feedback">{{ step.feedback }}</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- AI 改进建议 -->
        <el-card v-if="suggestions.length > 0" shadow="hover" class="suggestions-card">
          <template #header>
            <span class="card-title">💡 AI 改进建议</span>
          </template>
          <el-alert
            v-for="(suggestion, index) in suggestions"
            :key="index"
            :title="suggestion"
            type="warning"
            :closable="false"
            show-icon
            class="suggestion-item"
          />
        </el-card>

        <!-- 原始反馈 -->
        <el-card v-if="reportData.feedback" shadow="hover" class="feedback-card">
          <template #header>
            <span class="card-title">📄 AI 详细反馈</span>
          </template>
          <div class="feedback-content">{{ reportData.feedback }}</div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTrainingDetail } from '@/api/training'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const radarChartRef = ref(null)
let radarChart = null

// 训练记录完整信息
const trainingInfo = ref(null)

// 报告数据
const reportData = reactive({
  total_score: 0,
  dimension_scores: null,
  step_scores: [],
  feedback: ''
})

// 建议列表
const suggestions = ref([])

// 加载报告数据
const loadReportData = async () => {
  loading.value = true
  try {
    const res = await getTrainingDetail(route.params.id)
    
    // 保存完整训练信息
    trainingInfo.value = res
    
    // 解析评分数据
    reportData.total_score = parseFloat(res.total_score) || 0
    reportData.dimension_scores = res.dimension_scores || null
    reportData.feedback = res.feedback || ''
    
    // 解析步骤分数
    if (res.step_scores) {
      reportData.step_scores = Object.entries(res.step_scores)
        .filter(([key]) => !key.startsWith('_'))
        .map(([key, value]) => ({
          step_name: value.step_name || `步骤${key.replace('step', '')}`,
          score: parseFloat(value.score) || 0,
          feedback: value.feedback || ''
        }))
    }
    
    // AI 建议
    if (res.suggestions && res.suggestions.length > 0) {
      suggestions.value = res.suggestions
    } else {
      suggestions.value = []
    }
    
    // 渲染图表
    renderRadarChart()
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 渲染雷达图
const renderRadarChart = () => {
  if (!radarChartRef.value) return
  
  radarChart = echarts.init(radarChartRef.value)
  
  const dimensions = [
    { name: '动作完整性', score: reportData.dimension_scores?.action_completeness?.score ?? reportData.total_score },
    { name: '姿态规范性', score: reportData.dimension_scores?.pose_standardization?.score ?? reportData.total_score * 0.95 },
    { name: '操作时效性', score: reportData.dimension_scores?.timeliness?.score ?? reportData.total_score * 0.9 },
    { name: '总体评分', score: reportData.total_score }
  ]
  
  const option = {
    radar: {
      indicator: dimensions.map(d => ({ name: d.name, max: 100 })),
      radius: '65%',
      center: ['50%', '50%']
    },
    series: [{
      type: 'radar',
      data: [{
        value: dimensions.map(d => d.score),
        name: '评分',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        },
        lineStyle: {
          color: '#409eff',
          width: 2
        },
        itemStyle: {
          color: '#409eff'
        }
      }]
    }],
    tooltip: {
      trigger: 'item'
    }
  }
  
  radarChart.setOption(option)
}

// 辅助方法
const getTrainingTypeLabel = (type) => {
  const labels = {
    'fire_extinguisher': '灭火器操作',
    'extinguisher': '灭火器操作'
  }
  return labels[type] || type
}

const getStatusType = (status) => {
  const types = {
    'done': 'success',
    'completed': 'success',
    'in_progress': 'warning',
    'processing': 'info',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    'done': '已完成',
    'completed': '已完成',
    'in_progress': '进行中',
    'processing': '处理中',
    'failed': '失败'
  }
  return labels[status] || status
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getDimensionColor = (score) => {
  return getScoreColor(score)
}

const getScoreTagType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const getStepColor = (score) => {
  return getScoreColor(score)
}

onMounted(() => {
  loadReportData()
  window.addEventListener('resize', () => {
    radarChart?.resize()
  })
})

onUnmounted(() => {
  radarChart?.dispose()
})
</script>

<style scoped>
.admin-report-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 主内容区 */
.admin-report-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.breadcrumb {
  margin-bottom: 20px;
  color: #fff;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  color: rgba(255, 255, 255, 0.9);
}

.breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: #fff;
}

.report-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 卡片样式 */
.info-card,
.score-card,
.chart-card,
.steps-card,
.suggestions-card,
.feedback-card {
  border-radius: 12px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 评分卡片 */
.score-cards {
  margin-top: 0;
}

.score-card {
  text-align: center;
  padding: 20px;
  transition: transform 0.3s;
}

.score-card:hover {
  transform: translateY(-4px);
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}

.total-score .score-value {
  color: #409eff;
}

.score-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

/* 雷达图 */
.radar-chart {
  height: 350px;
}

/* 步骤列表 */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.step-item:hover {
  background: #ecf5ff;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
}

.step-feedback {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

/* 建议卡片 */
.suggestion-item {
  margin-bottom: 12px;
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

/* 反馈内容 */
.feedback-content {
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}
</style>
