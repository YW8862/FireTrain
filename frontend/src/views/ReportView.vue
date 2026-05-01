<template>
  <div class="app-page report-page">
    <NavBar />

    <div class="app-shell">
      <div class="report-topbar">
        <el-breadcrumb separator="/" class="report-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/history' }">训练历史</el-breadcrumb-item>
          <el-breadcrumb-item>训练报告</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="topbar-actions">
          <el-button
            type="primary"
            plain
            :loading="exporting"
            :disabled="loading"
            @click="handleExportPdf"
          >
            <el-icon><Download /></el-icon>
            <span>导出报告</span>
          </el-button>
          <el-button plain @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回</span>
          </el-button>
        </div>
      </div>

      <div ref="reportContentRef" v-loading="loading" class="report-body">
        <section class="hero-card">
          <div class="hero-left">
            <div class="hero-meta">
              <el-tag size="small" type="info" class="hero-id">
                记录 ID · {{ trainingInfo?.id ?? route.params.id }}
              </el-tag>
              <el-tag
                size="small"
                :type="getStatusType(trainingInfo?.status)"
                effect="light"
              >
                {{ getStatusLabel(trainingInfo?.status) }}
              </el-tag>
            </div>
            <h1 class="hero-title">
              {{ getTrainingTypeLabel(trainingInfo?.training_type) || '实操测评报告' }}
            </h1>
            <p class="hero-subtitle">
              系统基于训练视频分析结果，对本次实操过程进行多维度量化评估，并生成步骤得分、综合评价与改进建议。
            </p>

            <dl class="hero-facts">
              <div class="fact">
                <dt>训练项目</dt>
                <dd>
                  <el-icon class="fact-icon"><Document /></el-icon>
                  <span class="fact-strong">{{ getTrainingTypeLabel(trainingInfo?.training_type) || '-' }}</span>
                </dd>
              </div>
              <div class="fact">
                <dt>训练状态</dt>
                <dd>{{ getStatusLabel(trainingInfo?.status) }}</dd>
              </div>
              <div class="fact">
                <dt>开始时间</dt>
                <dd>{{ formatDateTime(trainingInfo?.created_at) }}</dd>
              </div>
              <div class="fact">
                <dt>完成时间</dt>
                <dd>{{ trainingInfo?.completed_at ? formatDateTime(trainingInfo?.completed_at) : '-' }}</dd>
              </div>
              <div class="fact">
                <dt>训练时长</dt>
                <dd>
                  <el-icon class="fact-icon"><Timer /></el-icon>
                  <span>{{ trainingInfo?.duration_seconds ? `${trainingInfo.duration_seconds} 秒` : '-' }}</span>
                </dd>
              </div>
              <div class="fact">
                <dt>评分时间</dt>
                <dd>{{ formatDateTime(trainingInfo?.completed_at || trainingInfo?.created_at) }}</dd>
              </div>
            </dl>
          </div>

          <div class="hero-right">
            <div class="score-ring">
              <svg viewBox="0 0 120 120" class="ring-svg">
                <circle cx="60" cy="60" r="52" class="ring-track" />
                <circle
                  cx="60"
                  cy="60"
                  r="52"
                  class="ring-value"
                  :stroke="getScoreColor(reportData.total_score)"
                  :stroke-dasharray="ringDasharray"
                />
              </svg>
              <div class="ring-content">
                <div class="ring-score" :style="{ color: getScoreColor(reportData.total_score) }">
                  {{ Math.round(reportData.total_score) }}
                </div>
                <div class="ring-label">综合得分</div>
              </div>
            </div>
            <el-tag
              :type="getPerformanceTagType(reportData.performance_level)"
              effect="dark"
              size="large"
              class="hero-level"
            >
              {{ getPerformanceLabel(reportData.performance_level) }}
            </el-tag>
          </div>
        </section>

        <section class="dim-grid">
          <div
            v-for="(dim, index) in dimensionItems"
            :key="dim.key"
            class="dim-card"
            :class="{ 'dim-card--empty': !dim.hasData }"
          >
            <div class="dim-card__header">
              <div class="dim-card__icon" :style="{ background: dimensionIconBg(index) }">
                <el-icon :size="18"><component :is="dimensionIcon(index)" /></el-icon>
              </div>
              <div class="dim-card__title">{{ dim.label }}</div>
            </div>
            <div class="dim-card__value" :style="{ color: dim.hasData ? getScoreColor(dim.score) : '#94a3b8' }">
              {{ dim.hasData ? dim.score.toFixed(1) : '—' }}
              <span v-if="dim.hasData" class="dim-card__unit">/100</span>
            </div>
            <div class="dim-card__bar">
              <div
                class="dim-card__bar-fill"
                :style="{
                  width: dim.hasData ? `${Math.min(100, Math.max(0, dim.score))}%` : '0%',
                  background: dim.hasData ? getScoreColor(dim.score) : '#e5e7eb'
                }"
              />
            </div>
            <div class="dim-card__comment">
              {{ dim.comment || (dim.hasData ? '表现较稳定，无额外评语' : '暂无维度数据') }}
            </div>
          </div>
        </section>

        <section class="analysis-row">
          <div class="analysis-card radar-wrapper">
            <div class="section-head">
              <div class="section-title">
                <el-icon class="section-title__icon"><DataAnalysis /></el-icon>
                <span>能力维度分析</span>
              </div>
              <span class="section-hint">总分与三项能力对比</span>
            </div>
            <div v-if="hasDimensionData" ref="radarChartRef" class="radar-chart"></div>
            <div v-else class="placeholder">
              <el-icon :size="36"><PieChart /></el-icon>
              <p>暂无能力维度数据</p>
            </div>
          </div>

          <div class="analysis-card steps-wrapper">
            <div class="section-head">
              <div class="section-title">
                <el-icon class="section-title__icon"><List /></el-icon>
                <span>步骤评分详情</span>
              </div>
              <span class="section-hint">共 {{ reportData.step_scores.length }} 个步骤</span>
            </div>

            <div v-if="reportData.step_scores.length > 0" class="step-list">
              <div
                v-for="(step, index) in reportData.step_scores"
                :key="index"
                class="step-row"
              >
                <div class="step-row__index">{{ index + 1 }}</div>
                <div class="step-row__body">
                  <div class="step-row__top">
                    <span class="step-row__name">{{ step.step_name }}</span>
                    <span
                      class="step-row__score"
                      :style="{ color: getScoreColor(step.score) }"
                    >
                      {{ Math.round(step.score) }}
                      <span class="step-row__score-unit">分</span>
                    </span>
                  </div>
                  <div class="step-row__bar">
                    <div
                      class="step-row__bar-fill"
                      :style="{
                        width: `${Math.min(100, Math.max(0, step.score))}%`,
                        background: getScoreColor(step.score)
                      }"
                    />
                  </div>
                  <p v-if="step.feedback" class="step-row__feedback">{{ step.feedback }}</p>
                </div>
              </div>
            </div>
            <div v-else class="placeholder placeholder--inline">
              <el-icon :size="28"><InfoFilled /></el-icon>
              <p>未提取到步骤评分</p>
            </div>
          </div>
        </section>

        <section class="analysis-card">
          <div class="section-head">
            <div class="section-title">
              <el-icon class="section-title__icon"><Opportunity /></el-icon>
              <span>训练改进建议</span>
            </div>
            <span class="section-hint">
              {{ suggestions.length > 0 ? `共 ${suggestions.length} 条` : '未生成建议' }}
            </span>
          </div>
          <ul v-if="suggestions.length > 0" class="suggestion-list">
            <li v-for="(item, index) in suggestions" :key="index" class="suggestion-item">
              <span class="suggestion-item__index">{{ index + 1 }}</span>
              <span class="suggestion-item__text">{{ item }}</span>
            </li>
          </ul>
          <div v-else class="placeholder placeholder--inline">
            <el-icon :size="28"><InfoFilled /></el-icon>
            <p>系统暂未生成改进建议</p>
          </div>
        </section>

        <section v-if="reportData.feedback" class="analysis-card">
          <div class="section-head">
            <div class="section-title">
              <el-icon class="section-title__icon"><ChatDotRound /></el-icon>
              <span>详细反馈</span>
            </div>
          </div>
          <div class="feedback-content">{{ reportData.feedback }}</div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Download,
  Timer,
  Document,
  DataAnalysis,
  PieChart,
  List,
  Opportunity,
  ChatDotRound,
  InfoFilled,
  Aim,
  Medal,
  Stopwatch
} from '@element-plus/icons-vue'
import { getTrainingDetail } from '@/api/training'
import { getTrainingTypeLabel } from '@/utils/trainingType'
import * as echarts from 'echarts'
import NavBar from '@/components/NavBar.vue'
import { buildReportPdfFilename, exportElementToPdf } from '@/utils/reportExport'
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

const loading = ref(false)
const exporting = ref(false)
const radarChartRef = ref(null)
const reportContentRef = ref(null)
let radarChart = null
let resizeHandler = null

const trainingInfo = ref(null)

const reportData = reactive({
  training_id: route.params.id,
  total_score: 0,
  performance_level: null,
  feedback: '',
  step_scores: [],
  dimension_scores: null,
  analysis_summary: null
})

const suggestions = ref([])
const dimensionItems = computed(() => getDimensionItems(reportData.dimension_scores))
const hasDimensionData = computed(() => hasDimensionScores(reportData.dimension_scores))
const currentUsername = computed(() => {
  if (trainingInfo.value?.username) return trainingInfo.value.username

  try {
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
    return userInfo.username || '用户'
  } catch {
    return '用户'
  }
})

const RING_CIRCUMFERENCE = 2 * Math.PI * 52
const ringDasharray = computed(() => {
  const ratio = Math.min(1, Math.max(0, reportData.total_score / 100))
  const value = RING_CIRCUMFERENCE * ratio
  return `${value} ${RING_CIRCUMFERENCE - value}`
})

const dimensionIconMap = [Aim, Medal, Stopwatch]
const dimensionIconBgMap = [
  'linear-gradient(135deg, #1e40af, #3b82f6)',
  'linear-gradient(135deg, #0f766e, #14b8a6)',
  'linear-gradient(135deg, #b45309, #f59e0b)'
]
const dimensionIcon = (idx) => dimensionIconMap[idx] || Aim
const dimensionIconBg = (idx) => dimensionIconBgMap[idx] || dimensionIconBgMap[0]

const loadReportData = async () => {
  loading.value = true
  try {
    const res = await getTrainingDetail(reportData.training_id)
    trainingInfo.value = res
    reportData.total_score = parseFloat(res.total_score) || 0
    reportData.performance_level = extractPerformanceLevel(res)
    reportData.dimension_scores = res.dimension_scores || null
    reportData.feedback = res.feedback || ''
    reportData.analysis_summary = res.analysis_summary || null
    reportData.step_scores = extractStepScores(res.step_scores)
    suggestions.value = normalizeSuggestions(res.suggestions)

    await nextTick()
    renderRadarChart()
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error(error.customMessage || error.response?.data?.detail || '加载报告失败')
  } finally {
    loading.value = false
  }
}

const renderRadarChart = () => {
  radarChart?.dispose()
  radarChart = null

  if (!radarChartRef.value || !hasDimensionData.value) return

  radarChart = echarts.init(radarChartRef.value)

  const dims = dimensionItems.value
  radarChart.setOption({
    tooltip: { trigger: 'item' },
    radar: {
      indicator: [
        { name: '动作完整性', max: 100 },
        { name: '姿态规范性', max: 100 },
        { name: '操作时效性', max: 100 },
        { name: '综合得分', max: 100 }
      ],
      radius: '66%',
      center: ['50%', '54%'],
      splitNumber: 4,
      axisName: {
        color: '#475569',
        fontSize: 12,
        fontWeight: 500
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(30, 64, 175, 0.02)', 'rgba(30, 64, 175, 0.05)']
        }
      },
      axisLine: {
        lineStyle: { color: 'rgba(30, 64, 175, 0.15)' }
      },
      splitLine: {
        lineStyle: { color: 'rgba(30, 64, 175, 0.15)' }
      }
    },
    series: [{
      type: 'radar',
      symbol: 'circle',
      symbolSize: 6,
      data: [{
        value: [
          dims[0]?.hasData ? dims[0].score : 0,
          dims[1]?.hasData ? dims[1].score : 0,
          dims[2]?.hasData ? dims[2].score : 0,
          reportData.total_score
        ],
        name: '本次评分',
        lineStyle: { color: '#1e40af', width: 2.5 },
        itemStyle: { color: '#1e40af' },
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.8, [
            { offset: 0, color: 'rgba(30, 64, 175, 0.35)' },
            { offset: 1, color: 'rgba(30, 64, 175, 0.05)' }
          ])
        }
      }]
    }]
  })
}

const goBack = () => {
  router.push('/history')
}

const getStatusType = (status) => ({
  done: 'success',
  completed: 'success',
  in_progress: 'warning',
  processing: 'info',
  failed: 'danger'
}[status] || 'info')

const getStatusLabel = (status) => ({
  done: '已完成',
  completed: '已完成',
  in_progress: '进行中',
  processing: '处理中',
  failed: '分析失败'
}[status] || status || '-')

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getScoreColor = (score) => {
  const s = Number(score) || 0
  if (s >= 85) return '#10b981'
  if (s >= 70) return '#2563eb'
  if (s >= 60) return '#f59e0b'
  return '#ef4444'
}

const handleExportPdf = async () => {
  if (!reportContentRef.value) return

  exporting.value = true
  try {
    const filename = buildReportPdfFilename(
      currentUsername.value,
      getTrainingTypeLabel(trainingInfo.value?.training_type) || '训练报告',
      trainingInfo.value?.id || route.params.id
    )

    await exportElementToPdf({
      element: reportContentRef.value,
      filename,
      beforeCapture: async () => {
        if (radarChart) {
          radarChart.resize()
          await new Promise(resolve => setTimeout(resolve, 300))
          if (typeof radarChart.getDataURL === 'function') {
            const dataURL = radarChart.getDataURL()
            if (dataURL) {
              const img = document.createElement('img')
              img.src = dataURL
              img.style.position = 'absolute'
              img.style.top = '0'
              img.style.left = '0'
              img.style.width = '100%'
              img.style.height = '100%'
              const radarDiv = radarChartRef.value
              if (radarDiv) {
                radarDiv.style.position = 'relative'
                radarDiv.appendChild(img)
              }
            }
          }
        }
      }
    })
    ElMessage.success('PDF 已开始下载')
  } catch (error) {
    console.error('导出 PDF 失败:', error)
    ElMessage.error(error.message || '导出 PDF 失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadReportData()
  resizeHandler = () => radarChart?.resize()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  radarChart?.dispose()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.report-page {
  padding-bottom: 24px;
}

.report-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.report-breadcrumb :deep(.el-breadcrumb__inner) {
  color: #475569;
  font-weight: 500;
}

.report-breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: #1e40af;
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 32px;
  padding: 32px 36px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.95) 0%, rgba(15, 23, 42, 0.92) 100%);
  color: #fff;
  overflow: hidden;
  box-shadow: 0 20px 60px -20px rgba(15, 23, 42, 0.3);
}

.hero-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 85% 15%, rgba(217, 33, 33, 0.25), transparent 45%),
    radial-gradient(circle at 10% 90%, rgba(59, 130, 246, 0.3), transparent 40%);
  pointer-events: none;
}

.hero-left,
.hero-right {
  position: relative;
  z-index: 1;
}

.hero-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.hero-meta :deep(.el-tag) {
  border: none;
  backdrop-filter: blur(6px);
}

.hero-id {
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: 0.5px;
}

.hero-subtitle {
  margin: 0 0 24px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  max-width: 520px;
  line-height: 1.7;
}

.hero-facts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px 32px;
  margin: 0;
}

.fact dt {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

.fact dd {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.fact-icon {
  opacity: 0.85;
}

.fact-strong {
  font-weight: 600;
  font-size: 16px;
}

.hero-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.score-ring {
  position: relative;
  width: 200px;
  height: 200px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.12);
  stroke-width: 10;
}

.ring-value {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dasharray 0.8s ease-out;
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.25));
}

.ring-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring-score {
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.ring-label {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  letter-spacing: 2px;
}

.hero-level {
  padding: 0 20px;
  height: 32px;
  line-height: 30px;
  font-size: 14px;
  font-weight: 600;
  border: none;
}

.dim-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.dim-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px 22px;
  border: 1px solid #eef1f6;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.dim-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}

.dim-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.dim-card__icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 6px 14px -6px rgba(30, 64, 175, 0.45);
}

.dim-card__title {
  font-size: 14px;
  color: #475569;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.dim-card__value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 12px;
}

.dim-card__unit {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
  margin-left: 4px;
}

.dim-card__bar {
  height: 6px;
  border-radius: 999px;
  background: #f1f5f9;
  overflow: hidden;
  margin-bottom: 10px;
}

.dim-card__bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease;
}

.dim-card__comment {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  min-height: 20px;
}

.analysis-row {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
}

.analysis-card {
  background: #fff;
  border-radius: 14px;
  padding: 22px 24px;
  border: 1px solid #eef1f6;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 14px;
  margin-bottom: 18px;
  border-bottom: 1px dashed #e5e7eb;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.section-title__icon {
  color: #1e40af;
  background: rgba(30, 64, 175, 0.1);
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.section-hint {
  font-size: 12px;
  color: #94a3b8;
}

.radar-chart {
  height: 360px;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 14px;
}

.placeholder--inline {
  padding: 24px 20px;
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.step-list::-webkit-scrollbar {
  width: 6px;
}

.step-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.step-row {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #eef1f6;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.step-row:hover {
  background: #f1f5ff;
  border-color: #c7d2fe;
}

.step-row__index {
  flex: 0 0 32px;
  height: 32px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #1e40af;
  font-size: 14px;
}

.step-row__body {
  flex: 1;
  min-width: 0;
}

.step-row__top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 12px;
}

.step-row__name {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-row__score {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}

.step-row__score-unit {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 2px;
  font-weight: 500;
}

.step-row__bar {
  height: 5px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.step-row__bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease;
}

.step-row__feedback {
  margin: 8px 0 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.suggestion-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(245, 158, 11, 0.02));
  border-left: 3px solid #f59e0b;
  border-radius: 8px;
  color: #334155;
  font-size: 14px;
  line-height: 1.7;
}

.suggestion-item__index {
  flex: 0 0 24px;
  height: 24px;
  border-radius: 50%;
  background: #f59e0b;
  color: #fff;
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.suggestion-item__text {
  flex: 1;
}

.feedback-content {
  padding: 16px 18px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #eef1f6;
  color: #475569;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
}

@media (max-width: 1100px) {
  .hero-card {
    grid-template-columns: 1fr;
    padding: 28px;
  }

  .hero-right {
    order: -1;
    flex-direction: row;
    justify-content: flex-start;
    gap: 24px;
  }

  .score-ring {
    width: 160px;
    height: 160px;
  }

  .ring-score {
    font-size: 44px;
  }

  .analysis-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .report-topbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .topbar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-facts {
    grid-template-columns: 1fr;
  }

  .dim-grid {
    grid-template-columns: 1fr;
  }
}
</style>
