<template>
  <div class="app-page report-page">
    <NavBar />

    <div class="app-shell app-shell--narrow">
    <el-card class="report-card section-card">
      <div class="report-header">
        <div class="header-left">
          <div>
            <h2>实操测评报告</h2>
            <p class="report-subtitle">查看本次训练总分、步骤表现和改进建议。</p>
          </div>
          <!-- 管理员视图标识 -->
          <el-tag v-if="isAdmin" type="warning" size="small" style="margin-left: 10px">
            <el-icon><UserFilled /></el-icon>
            管理员视图
          </el-tag>
        </div>
        <div class="header-right">
          <!-- 管理员返回管理后台 -->
          <el-button v-if="isAdmin" @click="goToAdminDashboard" type="primary">
            <el-icon><Back /></el-icon>
            返回管理后台
          </el-button>
          <!-- 普通用户返回首页 -->
          <el-button v-else @click="goBack">返回</el-button>
        </div>
      </div>

      <div v-loading="loading" class="report-content">
        <!-- 管理员视图：用户信息卡片 -->
        <el-card v-if="isAdmin && trainingInfo" shadow="hover" class="admin-info-card">
          <template #header>
            <div class="card-header">
              <span>👤 训练记录详情</span>
              <el-tag type="info" size="small">ID: {{ trainingInfo.id }}</el-tag>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="用户名">
              <el-tag type="primary">{{ trainingInfo.username }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="训练类型">
              {{ getTrainingTypeLabel(trainingInfo.training_type) }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(trainingInfo.status)">
                {{ getStatusLabel(trainingInfo.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatDateTime(trainingInfo.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间">
              {{ trainingInfo.completed_at ? formatDateTime(trainingInfo.completed_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="训练时长">
              {{ trainingInfo.duration_seconds ? `${trainingInfo.duration_seconds}秒` : '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 总分展示 -->
        <div class="total-score-section">
          <div class="score-title">{{ formatDate(new Date()) }}</div>
          <div class="score-display">
            <div class="score-number">{{ reportData.total_score }}</div>
            <div class="score-label">总分（分）</div>
          </div>
          <div class="score-percent">({{ reportData.total_score }}%)</div>
          <el-tag :type="getPerformanceTagType(reportData.performance_level)" size="large" class="level-tag">
            {{ getPerformanceLabel(reportData.performance_level) }}
          </el-tag>
        </div>

        <!-- 改进建议 -->
        <div class="feedback-section">
          <h2>训练改进建议</h2>
          <ul v-if="suggestions.length > 0" class="suggestion-list">
            <li v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item">
              <el-icon class="suggestion-icon"><SuccessFilled /></el-icon>
              {{ suggestion }}
            </li>
          </ul>
          <div v-else class="empty-data">暂无数据</div>
        </div>

        <!-- 整体反馈 -->
        <div v-if="reportData.feedback" class="feedback-section">
          <h2>整体反馈</h2>
          <p class="feedback-text">{{ reportData.feedback }}</p>
        </div>

        <!-- 分项评分 -->
        <div class="score-details-section">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="dimension-scores">
                <template v-if="hasDimensionData">
                  <div v-for="item in dimensionItems" :key="item.key" class="dimension-item">
                    <span class="dimension-label">{{ item.label }}</span>
                    <el-progress
                      v-if="item.hasData"
                      :percentage="item.score"
                      :color="getDimensionColor(item.score)"
                    />
                    <div v-else class="empty-data-inline">暂无数据</div>
                    <p v-if="item.comment" class="dimension-comment">
                      {{ item.comment }}
                    </p>
                  </div>
                </template>
                <div v-else class="empty-data">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <!-- 雷达图 -->
              <div v-if="hasDimensionData" ref="radarChartRef" class="chart-container"></div>
              <div v-else class="chart-empty-state">暂无数据</div>
            </el-col>
            <el-col :span="8">
              <!-- 步骤分数列表 -->
              <div class="step-scores-list">
                <template v-if="reportData.step_scores.length > 0">
                  <div v-for="(step, index) in reportData.step_scores" :key="index" class="step-score-item">
                    <div class="step-score-header">
                      <span class="step-score-name">{{ step.step_name }}</span>
                      <el-tag :type="getScoreTagType(step.score)" size="small">{{ step.score }}分</el-tag>
                    </div>
                    <el-progress 
                      :percentage="step.score" 
                      :color="getScoreColor(step.score)"
                      :show-text="false"
                      :stroke-width="4"
                    />
                    <p v-if="step.feedback" class="step-score-feedback">{{ step.feedback }}</p>
                  </div>
                </template>
                <div v-else class="empty-data">暂无数据</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SuccessFilled, UserFilled, Back } from '@element-plus/icons-vue'
import { getTrainingDetail } from '@/api/training'
import * as echarts from 'echarts'
import NavBar from '@/components/NavBar.vue'
import { getTrainingTypeLabel } from '@/utils/trainingType'
import {
  extractPerformanceLevel,
  extractStepScores,
  getDimensionItems,
  getPerformanceLabel,
  getPerformanceTagType,
  hasDimensionScores,
  normalizeSuggestions
} from '@/utils/trainingReport'

const route = useRoute()
const router = useRouter()

// 判断是否为管理员
const isAdmin = computed(() => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  return userInfo.role === 'admin' || userInfo.role === 'root'
})

const loading = ref(false)
const radarChartRef = ref(null)
let radarChart = null

// 训练记录完整信息（管理员视图）
const trainingInfo = ref(null)

// 报告数据
const reportData = reactive({
  training_id: route.params.id,
  total_score: 0,
  performance_level: null,
  feedback: '',
  step_scores: [],
  problems: [],
  suggestions: [],
  dimension_scores: null,
  analysis_summary: null
})

// 建议列表（从反馈中生成）
const suggestions = ref([])
const dimensionItems = computed(() => getDimensionItems(reportData.dimension_scores))
const hasDimensionData = computed(() => hasDimensionScores(reportData.dimension_scores))

// 获取分数标签类型
const getScoreTagType = (score) => {
  const scoreNum = typeof score === 'string' ? parseFloat(score) : score
  if (scoreNum >= 90) return 'success'
  if (scoreNum >= 80) return 'success'
  if (scoreNum >= 60) return 'warning'
  return 'danger'
}

// 加载报告数据
const loadReportData = async () => {
  loading.value = true
  try {
    const res = await getTrainingDetail(reportData.training_id)
    
    // 保存完整训练信息（管理员视图）
    trainingInfo.value = res
    
    // 解析数据 - 处理字符串到数字的转换
    reportData.total_score = parseFloat(res.total_score) || 0
    reportData.feedback = res.feedback || ''

    // 维度分数（LLM 评分时返回）
    reportData.dimension_scores = res.dimension_scores || null
    reportData.analysis_summary = res.analysis_summary || null

    reportData.performance_level = extractPerformanceLevel(res)
    reportData.step_scores = extractStepScores(res.step_scores)

    suggestions.value = normalizeSuggestions(res.suggestions)
    
    // 渲染图表
    renderRadarChart()
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error(error.customMessage || error.response?.data?.detail || '加载报告失败')
  } finally {
    loading.value = false
  }
}

// 渲染雷达图
const renderRadarChart = () => {
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }

  if (!radarChartRef.value || !hasDimensionData.value) {
    return
  }

  radarChart = echarts.init(radarChartRef.value)
  
  const indicators = [
    { name: '动作完整性', max: 100 },
    { name: '姿态规范性', max: 100 },
    { name: '操作时效性', max: 100 }
  ]

  const data = [
    dimensionItems.value[0].score ?? 0,
    dimensionItems.value[1].score ?? 0,
    dimensionItems.value[2].score ?? 0
  ]
  
  const option = {
    title: {
      text: '各维度评分雷达图',
      left: 'center',
      top: 10
    },
    radar: {
      indicator: indicators,
      shape: 'circle',
      splitNumber: 5
    },
    series: [{
      name: '评分',
      type: 'radar',
      data: [{
        value: data,
        name: '本次训练'
      }],
      areaStyle: {
        color: 'rgba(64, 158, 255, 0.5)'
      },
      lineStyle: {
        color: '#409EFF'
      }
    }]
  }
  
  radarChart.setOption(option)
}

// 返回上一页
const goBack = () => {
  router.push('/history')
}

// 管理员返回管理后台
const goToAdminDashboard = () => {
  router.push('/admin/dashboard')
}

// 获取训练类型标签
// 获取状态标签类型
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

// 获取状态标签文本
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

// 格式化日期时间
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

// 格式化日期
const formatDate = (date) => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取维度颜色
const getDimensionColor = (score) => {
  const scoreNum = typeof score === 'string' ? parseFloat(score) : score
  if (scoreNum >= 90) return '#67C23A'
  if (scoreNum >= 80) return '#67C23A'
  if (scoreNum >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取分数颜色
const getScoreColor = (score) => {
  const scoreNum = typeof score === 'string' ? parseFloat(score) : score
  if (scoreNum >= 90) return '#67C23A'
  if (scoreNum >= 80) return '#67C23A'
  if (scoreNum >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 组件挂载时加载数据
onMounted(() => {
  loadReportData()
})

// 组件卸载时清理图表
onUnmounted(() => {
  if (radarChart) {
    radarChart.dispose()
  }
})
</script>

<style scoped>
.report-page {
  padding-bottom: 24px;
}

.report-card {
  margin: 0;
}

/* 管理员信息卡片 */
.admin-info-card {
  margin-bottom: 24px;
  border-left: 4px solid #409eff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e4e7ed;
}

.report-subtitle {
  margin: 8px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.report-content {
  padding: 10px;
}

.total-score-section {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: linear-gradient(180deg, rgba(30, 64, 175, 0.96), rgba(30, 64, 175, 0.84));
  border-radius: 12px;
  color: #fff;
}

.score-title {
  font-size: 16px;
  margin-bottom: 15px;
  opacity: 0.9;
}

.score-display {
  display: inline-block;
  margin-bottom: 10px;
}

.score-number {
  font-size: 72px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  margin-top: 5px;
  opacity: 0.9;
}

.score-percent {
  display: block;
  font-size: 18px;
  margin-bottom: 15px;
  opacity: 0.9;
}

.level-tag {
  margin-top: 10px;
}

.feedback-section {
  margin: 24px 0;
  padding: 20px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 12px;
  border-left: 4px solid #f59e0b;
}

.feedback-section h2 {
  font-size: 20px;
  font-weight: 600;
  color: #92400e;
  margin: 0 0 16px 0;
}

.feedback-text {
  margin: 0;
  color: #78350f;
  line-height: 1.8;
  white-space: pre-wrap;
}

.suggestion-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  font-size: 15px;
  color: #78350f;
  line-height: 1.6;
  border-bottom: 1px solid rgba(245, 158, 11, 0.2);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-icon {
  font-size: 20px;
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 2px;
}

.score-details-section {
  margin-bottom: 30px;
}

.dimension-scores {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.dimension-item {
  margin-bottom: 20px;
}

.dimension-item:last-child {
  margin-bottom: 0;
}

.dimension-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #303133;
}

.dimension-comment {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #909399;
}

.empty-data,
.chart-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.empty-data-inline {
  color: #909399;
  font-size: 13px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.chart-empty-state {
  height: 300px;
  background: #f5f7fa;
  border-radius: 8px;
}

.step-scores-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.step-score-item {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 6px;
}

.step-score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-score-name {
  font-weight: 500;
  color: #303133;
}

.step-score-feedback {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
