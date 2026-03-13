<template>
  <div class="report-container">
    <!-- 顶部导航栏 -->
    <NavBar />

    <el-card class="report-card">
      <div class="report-header">
        <h2>📊 训练评分报告</h2>
        <el-button @click="goBack">返回</el-button>
      </div>

      <div v-loading="loading" class="report-content">
        <!-- 总分展示 -->
        <div class="total-score-section">
          <div class="score-title">{{ formatDate(new Date()) }}</div>
          <div class="score-display">
            <div class="score-number">{{ reportData.total_score }}</div>
            <div class="score-label">总分（分）</div>
          </div>
          <div class="score-percent">({{ reportData.total_score }}%)</div>
          <el-tag :type="getLevelTagType(reportData.performance_level)" size="large" class="level-tag">
            {{ reportData.performance_level === 'excellent' ? '优秀' :
               reportData.performance_level === 'good' ? '良好' :
               reportData.performance_level === 'pass' ? '合格' : '待改进' }}
          </el-tag>
        </div>

        <!-- 反馈建议 -->
        <div v-if="reportData.feedback" class="feedback-section">
          <h2>💡 改进建议</h2>
          <ul class="suggestion-list">
            <li v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item">
              <el-icon class="suggestion-icon"><SuccessFilled /></el-icon>
              {{ suggestion }}
            </li>
          </ul>
        </div>

        <!-- 分项评分 -->
        <div class="score-details-section">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="dimension-scores">
                <div class="dimension-item">
                  <span class="dimension-label">动作完整性</span>
                  <el-progress :percentage="reportData.total_score" :color="getDimensionColor(reportData.total_score)" />
                </div>
                <div class="dimension-item">
                  <span class="dimension-label">姿态规范性</span>
                  <el-progress :percentage="reportData.total_score * 0.95" :color="getDimensionColor(reportData.total_score * 0.95)" />
                </div>
                <div class="dimension-item">
                  <span class="dimension-label">操作时效性</span>
                  <el-progress :percentage="reportData.total_score * 0.9" :color="getDimensionColor(reportData.total_score * 0.9)" />
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <!-- 雷达图 -->
              <div ref="radarChartRef" class="chart-container"></div>
            </el-col>
            <el-col :span="8">
              <!-- 步骤分数列表 -->
              <div class="step-scores-list">
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
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, SuccessFilled } from '@element-plus/icons-vue'
import { getTrainingDetail } from '@/api/training'
import * as echarts from 'echarts'
import NavBar from '@/components/NavBar.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const radarChartRef = ref(null)
let radarChart = null

// 报告数据
const reportData = reactive({
  training_id: route.params.id,
  total_score: 0,
  performance_level: 'pass',
  feedback: '',
  step_scores: [],
  problems: [],
  suggestions: []
})

// 建议列表（从反馈中生成）
const suggestions = ref([])

// 获取等级图标
const getLevelIcon = (level) => {
  const icons = {
    excellent: 'SuccessFilled',
    good: 'CircleCheckFilled',
    pass: 'InfoFilled',
    fail: 'CircleCloseFilled'
  }
  return icons[level] || 'InfoFilled'
}

// 获取等级标题
const getLevelTitle = (level) => {
  const titles = {
    excellent: '表现优秀',
    good: '表现良好',
    pass: '基本合格',
    fail: '需要改进'
  }
  return titles[level] || '完成训练'
}

// 获取等级标签类型
const getLevelTagType = (level) => {
  const types = {
    excellent: 'success',
    good: 'success',
    pass: 'warning',
    fail: 'danger'
  }
  return types[level] || 'info'
}

// 获取分数标签类型
const getScoreTagType = (score) => {
  const scoreNum = typeof score === 'string' ? parseFloat(score) : score
  if (scoreNum >= 90) return 'success'
  if (scoreNum >= 80) return 'success'
  if (scoreNum >= 60) return 'warning'
  return 'danger'
}

// 获取步骤颜色
const getStepColor = (score) => {
  const scoreNum = typeof score === 'string' ? parseFloat(score) : score
  if (scoreNum >= 90) return '#67C23A'
  if (scoreNum >= 80) return '#67C23A'
  if (scoreNum >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 加载报告数据
const loadReportData = async () => {
  loading.value = true
  try {
    const res = await getTrainingDetail(reportData.training_id)
    
    // 解析数据 - 处理字符串到数字的转换
    reportData.total_score = parseFloat(res.total_score) || 0
    reportData.feedback = res.feedback || ''
    
    // 根据总分确定等级
    if (res.total_score >= 90) {
      reportData.performance_level = 'excellent'
    } else if (res.total_score >= 80) {
      reportData.performance_level = 'good'
    } else if (res.total_score >= 60) {
      reportData.performance_level = 'pass'
    } else {
      reportData.performance_level = 'fail'
    }
    
    // 解析步骤分数 - 将对象转换为数组
    if (res.step_scores) {
      // API 返回的是对象 {step1: {...}, step2: {...}}，需要转换为数组
      reportData.step_scores = Object.entries(res.step_scores).map(([key, value]) => ({
        step_name: value.step_name || `步骤${key.replace('step', '')}`,
        score: parseFloat(value.score) || 0,
        feedback: value.feedback || ''
      }))
    }
    
    // 从反馈中生成问题列表和建议（简化处理）
    if (res.feedback) {
      // TODO: 使用真实的 AI 反馈生成器结果
      reportData.problems = ['部分动作不够规范，需要加强练习']
      reportData.suggestions = [
        '步骤 2 拔销动作不够流畅，建议练习手腕发力',
        '步骤 4 手臂角度偏差 5 度，请保持手臂伸直',
        '整体操作时间优秀，继续保持'
      ]
      suggestions.value = reportData.suggestions
    } else {
      suggestions.value = []
    }
    
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
  if (!radarChartRef.value) return
  
  // 初始化图表
  radarChart = echarts.init(radarChartRef.value)
  
  // 准备数据 - 确保 step_scores 是数组
  if (!Array.isArray(reportData.step_scores) || reportData.step_scores.length === 0) {
    console.warn('步骤分数数据格式不正确')
    return
  }
  
  const indicators = reportData.step_scores.map(step => ({
    name: step.step_name,
    max: 100
  }))
  
  const data = reportData.step_scores.map(step => step.score)
  
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
.report-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
}

.report-card {
  max-width: 1200px;
  margin: 20px auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.report-content {
  padding: 10px;
}

.total-score-section {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
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

.chart-container {
  height: 300px;
  width: 100%;
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
  .report-container {
    padding: 10px;
  }
}
</style>
