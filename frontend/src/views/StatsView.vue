<template>
  <div class="stats-container">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <h1>📊 数据统计</h1>
          <el-button @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </template>

      <div v-loading="loading" class="stats-content">
        <!-- 个人统计概览 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :span="6">
            <el-statistic title="总训练次数" :value="stats.total_training_count">
              <template #suffix>次</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均分数" :value="stats.average_score" :precision="1">
              <template #suffix>分</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="最佳成绩" :value="stats.best_score" :precision="1">
              <template #suffix>分</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="最近训练" :value="formatDate(stats.last_training_date)" />
          </el-col>
        </el-row>

        <!-- 成绩趋势图 -->
        <el-card shadow="hover" class="mb-4">
          <template #header>
            <div class="chart-header">
              <span>📈 成绩趋势（最近 {{ trendDays }} 天）</span>
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
            <el-card shadow="hover">
              <template #header>
                <span>📊 步骤分对比</span>
              </template>
              <div ref="stepBarChartRef" class="chart-container-small"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>🎯 能力维度雷达图</span>
              </template>
              <div ref="radarChartRef" class="chart-container-small"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 步骤分析 -->
        <el-card shadow="hover" v-if="stepAnalysis && stepAnalysis.length > 0">
          <template #header>
            <span>📋 各步骤表现分析</span>
          </template>
          <el-table :data="stepAnalysis" style="width: 100%">
            <el-table-column prop="step_name" label="步骤名称" width="180" />
            <el-table-column prop="average_score" label="平均分" width="100" sortable>
              <template #default="{ row }">
                <el-tag :type="getScoreTagType(row.average_score)">
                  {{ row.average_score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="training_count" label="训练次数" width="100" />
            <el-table-column prop="success_rate" label="成功率" width="100">
              <template #default="{ row }">
                {{ (row.success_rate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="改进建议" />
          </el-table>
        </el-card>

        <!-- 空状态 -->
        <el-empty v-if="!loading && !stats.total_training_count" description="暂无训练数据，快去训练吧！">
          <el-button type="primary" @click="goToTraining">开始训练</el-button>
        </el-empty>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  getPersonalStatistics,
  getTrainingTrend,
  getStepAnalysis
} from '@/api/statistics'

const router = useRouter()

const loading = ref(false)
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

// 获取分数标签类型
const getScoreTagType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未训练'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 加载所有数据
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadPersonalStats(),
      loadTrendData(),
      loadStepAnalysis()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载个人统计
const loadPersonalStats = async () => {
  try {
    const res = await getPersonalStatistics()
    stats.total_training_count = res.total_training_count || 0
    stats.average_score = parseFloat(res.average_score) || 0
    stats.best_score = parseFloat(res.best_score) || 0
    stats.last_training_date = res.last_training_date
  } catch (error) {
    console.error('加载个人统计失败:', error)
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  try {
    const res = await getTrainingTrend(trendDays.value)
    renderTrendChart(res.trend_data)
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  }
}

// 加载步骤分析
const loadStepAnalysis = async () => {
  try {
    const res = await getStepAnalysis()
    stepAnalysis.value = res.step_analysis || []
    renderStepBarChart(res.step_analysis)
    renderRadarChart(res.step_analysis)
  } catch (error) {
    console.error('加载步骤分析失败:', error)
  }
}

// 渲染趋势图（折线图）
const renderTrendChart = (data) => {
  if (!trendChartRef.value) return
  
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }
  
  const dates = data.map(item => item.date)
  const scores = data.map(item => item.average_score)
  const counts = data.map(item => item.training_count)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
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
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
const renderStepBarChart = (data) => {
  if (!stepBarChartRef.value) return
  
  if (!stepBarChart) {
    stepBarChart = echarts.init(stepBarChartRef.value)
  }
  
  const steps = data.map(item => item.step_name)
  const scores = data.map(item => parseFloat(item.average_score))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
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
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
const renderRadarChart = (data) => {
  if (!radarChartRef.value) return
  
  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }
  
  const indicator = data.map(item => ({
    name: item.step_name,
    max: 100
  }))
  
  const values = data.map(item => parseFloat(item.average_score))
  
  const option = {
    tooltip: {},
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

// 跳转到训练页面
const goToTraining = () => {
  router.push('/training')
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})

// 窗口大小变化时重新渲染图表
window.addEventListener('resize', () => {
  trendChart && trendChart.resize()
  stepBarChart && stepBarChart.resize()
  radarChart && radarChart.resize()
})

// 组件卸载时清理图表
onUnmounted(() => {
  trendChart && trendChart.dispose()
  stepBarChart && stepBarChart.dispose()
  radarChart && radarChart.dispose()
})
</script>

<style scoped>
.stats-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.stats-card {
  max-width: 1400px;
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

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.chart-container-small {
  height: 250px;
  width: 100%;
}
</style>
