<template>
  <div class="app-page stats-page">
    <NavBar />

    <div class="app-shell">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <div>
            <h1 class="page-title">训练统计分析</h1>
            <p class="page-subtitle">查看训练次数、平均得分、趋势变化和各步骤表现。</p>
          </div>
          <div class="card-header-actions">
            <el-select v-model="selectedTrainingType" placeholder="全部训练项目" clearable size="small" @change="loadData">
              <el-option
                v-for="option in TRAINING_TYPE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-button @click="loadData" :loading="loading">刷新数据</el-button>
          </div>
        </div>
      </template>

      <div class="stats-content">
        <!-- 个人统计概览 -->
        <el-row :gutter="20" class="mb-4" v-loading="personalLoading">
          <el-col :span="6">
            <el-statistic title="训练总次数" :value="stats.total_training_count">
              <template #suffix>次</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均得分" :value="stats.average_score" :precision="1">
              <template #suffix>分</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="最佳得分" :value="stats.best_score" :precision="1">
              <template #suffix>分</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="最近训练" :value="formatDate(stats.last_training_date)" />
          </el-col>
        </el-row>

        <!-- 成绩趋势图 -->
        <el-card shadow="hover" class="mb-4" v-loading="trendLoading">
          <template #header>
            <div class="chart-header">
              <span>实操得分趋势（最近 {{ trendDays }} 天）</span>
              <el-select v-model="trendDays" size="small" @change="loadTrendData">
                <el-option label="最近 7 天" :value="7" />
                <el-option label="最近 15 天" :value="15" />
                <el-option label="最近 30 天" :value="30" />
              </el-select>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>

        <!-- 步骤分对比图 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :span="12">
            <el-card shadow="hover" v-loading="stepLoading">
              <template #header>
                <span>各步骤得分分布</span>
              </template>
              <div ref="stepBarChartRef" class="chart-container-small"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" v-loading="stepLoading">
              <template #header>
                <span>能力维度概览</span>
              </template>
              <div ref="radarChartRef" class="chart-container-small"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 步骤分析 -->
        <el-card shadow="hover" v-loading="stepLoading" v-if="stepAnalysis && stepAnalysis.length > 0">
          <template #header>
            <div class="card-header">
              <span>步骤表现分析</span>
            </div>
          </template>
          <el-table 
            :data="stepAnalysis" 
            style="width: 100%"
            :cell-style="{ padding: '12px 8px' }"
          >
            <el-table-column prop="step_name" label="步骤名称" width="200" />
            <el-table-column prop="average_score" label="平均分" width="120" sortable align="center">
              <template #default="{ row }">
                <el-tag :type="getScoreTagType(row.average_score)" size="large">
                  {{ row.average_score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="training_count" label="训练次数" width="120" align="center" />
            <el-table-column prop="success_rate" label="成功率" width="120" sortable align="center">
              <template #default="{ row }">
                <span class="success-rate">{{ Number(row.success_rate).toFixed(1) }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="改进建议" min-width="280">
              <template #default="{ row }">
                <span class="suggestion-text">{{ row.suggestion }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getStatisticsOverview,
  getTrainingTrend,
  getStepAnalysis
} from '@/api/statistics'
import { useTrainingTypes } from '@/composables/useTrainingTypes'
import NavBar from '@/components/NavBar.vue'

const { TRAINING_TYPE_OPTIONS } = useTrainingTypes()
const selectedTrainingType = ref(null)

let echarts = null
let echartsLoader = null

const ensureEcharts = async () => {
  if (echarts) return echarts
  if (!echartsLoader) {
    echartsLoader = import('echarts').then((mod) => {
      echarts = mod
      return mod
    })
  }
  return echartsLoader
}

const personalLoading = ref(false)
const trendLoading = ref(false)
const stepLoading = ref(false)
const loading = computed(() =>
  personalLoading.value || trendLoading.value || stepLoading.value
)
const trendDays = ref(7)
const trendChartRef = ref(null)
const stepBarChartRef = ref(null)
const radarChartRef = ref(null)

let trendChart = null
let stepBarChart = null
let radarChart = null

// 统计数据
const stats = reactive({
  total_training_count: 0,
  average_score: 0,
  best_score: 0,
  last_training_date: null
})

// 步骤分析
const stepAnalysis = ref([])

const normalizeSuccessRate = (value) => {
  const rate = Number(value || 0)
  if (Number.isNaN(rate)) return 0
  return rate > 1 ? rate / 100 : rate
}

const normalizeStepAnalysis = (items = []) => {
  return items.map(item => ({
    ...item,
    training_count: item.training_count || 0,
    suggestion: item.suggestion || item.improvement_suggestion || '继续保持规范操作',
    success_rate: normalizeSuccessRate(item.success_rate),
    average_score: parseFloat(item.average_score) || 0
  }))
}

const resetPersonalStats = () => {
  stats.total_training_count = 0
  stats.average_score = 0
  stats.best_score = 0
  stats.last_training_date = null
}

const applyPersonalStats = (res = {}) => {
  stats.total_training_count = res.total_training_count || res.total_trainings || 0
  stats.average_score = parseFloat(res.average_score) || 0
  stats.best_score = parseFloat(res.best_score) || 0
  stats.last_training_date = res.last_training_date || res.last_training_at || null
}

const applyOverviewData = async (overview = {}) => {
  applyPersonalStats(overview.personal_stats || {})
  stepAnalysis.value = normalizeStepAnalysis(overview.step_analysis?.step_analysis || [])
  await Promise.all([
    renderTrendChart(overview.recent_trend?.trend_data || []),
    renderStepBarChart(stepAnalysis.value),
    renderRadarChart(stepAnalysis.value)
  ])
}

const buildEmptyChartGraphic = (text) => ({
  type: 'text',
  left: 'center',
  top: 'middle',
  silent: true,
  style: {
    text,
    fill: '#909399',
    fontSize: 16,
    fontWeight: 500
  }
})

// 获取分数标签类型
const getScoreTagType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 获取等级标签类型
// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未训练'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载所有数据
const loadData = async () => {
  personalLoading.value = true
  trendLoading.value = true
  stepLoading.value = true
  try {
    const overview = await getStatisticsOverview(trendDays.value, selectedTrainingType.value)
    await applyOverviewData(overview)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载数据失败')
    resetPersonalStats()
    stepAnalysis.value = []
  } finally {
    personalLoading.value = false
    trendLoading.value = false
    stepLoading.value = false
  }
}

// 加载个人统计
const loadPersonalStats = async () => {
  personalLoading.value = true
  try {
    const overview = await getStatisticsOverview(trendDays.value)
    applyPersonalStats(overview.personal_stats || {})
  } catch (error) {
    resetPersonalStats()
    console.error('加载个人统计失败:', error)
  } finally {
    personalLoading.value = false
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  trendLoading.value = true
  try {
    const res = await getTrainingTrend(trendDays.value)
    await renderTrendChart(res.trend_data || [])
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  } finally {
    trendLoading.value = false
  }
}

// 加载步骤分析
const loadStepAnalysis = async () => {
  stepLoading.value = true
  try {
    const res = await getStepAnalysis(selectedTrainingType.value)
    stepAnalysis.value = normalizeStepAnalysis(res.step_analysis || [])
    await Promise.all([
      renderStepBarChart(stepAnalysis.value),
      renderRadarChart(stepAnalysis.value)
    ])
  } catch (error) {
    console.error('加载步骤分析失败:', error)
  } finally {
    stepLoading.value = false
  }
}

// 渲染趋势图（折线图）
const renderTrendChart = async (data) => {
  if (!trendChartRef.value) return
  const chartLib = await ensureEcharts()

  if (!trendChart) {
    trendChart = chartLib.init(trendChartRef.value)
  }

  const dates = data.map(item => item.date)
  const scores = data.map(item => item.average_score)
  const counts = data.map(item => item.training_count)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      position: (point, params, dom, rect, size) => {
        // 动态调整位置，避免被遮挡
        let x = point[0] + 10
        let y = point[1] - 40
        
        // 如果靠近顶部，显示在下方
        if (y < 100) {
          y = point[1] + 20
        }
        
        return [x, y]
      },
      confine: false,
      extraCssText: 'z-index: 10000;'
    },
    legend: {
      data: ['平均分数', '训练次数'],
      top: 10
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '分数',
        min: 0,
        max: 100
      },
      {
        type: 'value',
        name: '次数',
        min: 0
      }
    ],
    series: [
      {
        name: '平均分数',
        type: 'line',
        yAxisIndex: 0,
        data: scores,
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new chartLib.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      },
      {
        name: '训练次数',
        type: 'line',
        yAxisIndex: 1,
        data: counts,
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
  
  trendChart.setOption(option)
}

// 渲染步骤对比图（柱状图）
const renderStepBarChart = async (data) => {
  if (!stepBarChartRef.value) return
  const chartLib = await ensureEcharts()

  if (!stepBarChart) {
    stepBarChart = chartLib.init(stepBarChartRef.value)
  }

  if (!data.length) {
    stepBarChart.setOption({
      title: {
        text: '暂无步骤数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#909399',
          fontSize: 16,
          fontWeight: 500
        }
      },
      xAxis: { show: false, type: 'category', data: [] },
      yAxis: { show: false, type: 'value' },
      series: []
    }, true)
    return
  }
  
  const steps = data.map(item => item.step_name)
  const scores = data.map(item => parseFloat(item.average_score))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      position: (point, params, dom, rect, size) => {
        // 动态调整位置，避免被遮挡
        let x = point[0] + 10
        let y = point[1] - 40
        
        // 如果靠近顶部，显示在下方
        if (y < 100) {
          y = point[1] + 20
        }
        
        return [x, y]
      },
      confine: false,
      extraCssText: 'z-index: 10000;'
    },
    xAxis: {
      type: 'category',
      data: steps,
      axisLabel: {
        interval: 0,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100
    },
    series: [
      {
        name: '平均分',
        type: 'bar',
        data: scores,
        itemStyle: {
          color: new chartLib.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#409EFFaa' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}分'
        }
      }
    ]
  }
  
  stepBarChart.setOption(option)
}

// 渲染雷达图
const renderRadarChart = async (data) => {
  if (!radarChartRef.value) return
  const chartLib = await ensureEcharts()

  if (!radarChart) {
    radarChart = chartLib.init(radarChartRef.value)
  }

  if (!data.length) {
    radarChart.setOption({
      graphic: [buildEmptyChartGraphic('暂无步骤数据')],
      radar: {
        indicator: [{ name: '暂无数据', max: 100 }],
        shape: 'circle',
        splitNumber: 5
      },
      series: []
    }, true)
    return
  }
  
  const indicator = data.map(item => ({
    name: item.step_name,
    max: 100
  }))
  
  const values = data.map(item => parseFloat(item.average_score))
  
  const option = {
    graphic: [],
    tooltip: {
      trigger: 'item',
      position: (point, params, dom, rect, size) => {
        // 根据鼠标位置动态调整，确保完全可见
        let x = point[0] + 15
        let y = point[1] - 30
        
        // 如果靠近顶部，显示在下方
        if (y < 120) {
          y = point[1] + 20
        }
        
        return [x, y]
      },
      confine: false,
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      borderRadius: 8,
      padding: [12, 16],
      extraCssText: 'z-index: 10000; box-shadow: 0 4px 16px rgba(0,0,0,0.15);',
      formatter: (params) => {
        const value = params.value
        const name = params.name
        const score = typeof value === 'number' ? value : parseFloat(value)
        
        // 获取等级和颜色
        let level, color
        if (score >= 90) {
          level = '优秀'
          color = '#67C23A'
        } else if (score >= 80) {
          level = '良好'
          color = '#409EFF'
        } else if (score >= 60) {
          level = '合格'
          color = '#E6A23C'
        } else {
          level = '待改进'
          color = '#F56C6C'
        }
        
        return `
          <div style="font-weight: 600; margin-bottom: 8px; color: #303133; font-size: 14px;">${name}</div>
          <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px; align-items: center;">
            <span style="color: #64748b; font-size: 13px;">得分:</span>
            <span style="font-weight: 600; color: ${color}; font-size: 15px;">${score}分</span>
            
            <span style="color: #64748b; font-size: 13px;">等级:</span>
            <span style="color: ${color}; font-weight: 500; font-size: 13px;">${level}</span>
            
            <span style="color: #64748b; font-size: 13px;">满分:</span>
            <span style="color: #303133; font-size: 13px;">100分</span>
          </div>
        `
      }
    },
    radar: {
      indicator: indicator,
      shape: 'circle',
      splitNumber: 5
    },
    series: [
      {
        name: '步骤表现',
        type: 'radar',
        data: [
          {
            value: values,
            name: '平均表现'
          }
        ],
        areaStyle: {
          color: 'rgba(67, 194, 58, 0.5)'
        },
        lineStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
  
  radarChart.setOption(option)
}

const handleResize = () => {
  trendChart && trendChart.resize()
  stepBarChart && stepBarChart.resize()
  radarChart && radarChart.resize()
}

// 组件挂载时加载数据
onMounted(() => {
  // 先让页面完成切换和首屏渲染，再异步加载统计数据与图表资源。
  requestAnimationFrame(() => {
    loadData()
  })
})

// 窗口大小变化时重新渲染图表
window.addEventListener('resize', handleResize)

// 组件卸载时清理图表
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart && trendChart.dispose()
  stepBarChart && stepBarChart.dispose()
  radarChart && radarChart.dispose()
})
</script>

<style scoped>
.stats-page {
  padding-bottom: 24px;
}

.stats-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px 20px;
  display: flex;
  flex-direction: column;
}

.stats-card {
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 8px;
}

.card-header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-header-actions .el-select {
  min-width: 160px;
}

.card-header-actions .el-select .el-input__wrapper {
  font-size: 14px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--ft-color-text-primary);
  margin: 0;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
}

.mb-4 {
  margin-bottom: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-content {
  padding: 24px;
}

/* 统计卡片美化 */
:deep(.el-statistic) {
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
  transition: all 0.3s ease;
}

:deep(.el-statistic:hover) {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
}

:deep(.el-statistic__title) {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 8px;
}

:deep(.el-statistic__content) {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

/* 表格美化 */
:deep(.el-table) {
  font-size: 15px;
}

:deep(.el-table th) {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
  color: #475569;
  font-weight: 600;
  font-size: 15px;
  padding: 14px 8px !important;
}

:deep(.el-table td) {
  padding: 14px 8px !important;
  color: #334155;
}

:deep(.el-table tr:hover) {
  background-color: #f8fafc !important;
}

.success-rate {
  font-weight: 600;
  color: #059669;
  font-size: 15px;
}

.suggestion-text {
  color: #64748b;
  line-height: 1.6;
  display: block;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.chart-container-small {
  height: 300px;
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-container {
    padding: 15px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  :deep(.el-statistic) {
    padding: 12px;
  }
  
  :deep(.el-statistic__content) {
    font-size: 24px;
  }
}
</style>
