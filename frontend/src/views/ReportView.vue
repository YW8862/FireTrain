<template>
  <div class="report-container">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <h1>📊 训练报告</h1>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>

      <div v-loading="loading" class="report-content">
        <!-- 总分展示 -->
        <div class="total-score-section">
          <el-result
            :icon="getLevelIcon(reportData.performance_level)"
            :title="getLevelTitle(reportData.performance_level)"
            :sub-title="`总分：${reportData.total_score} / 100`"
          >
            <template #extra>
              <el-tag :type="getLevelTagType(reportData.performance_level)" size="large">
                {{ reportData.performance_level === 'excellent' ? '优秀' :
                   reportData.performance_level === 'good' ? '良好' :
                   reportData.performance_level === 'pass' ? '合格' : '待改进' }}
              </el-tag>
            </template>
          </el-result>
        </div>

        <!-- 反馈建议 -->
        <div v-if="reportData.feedback" class="feedback-section">
          <h2>💡 总体反馈</h2>
          <el-alert :title="reportData.feedback" type="success" :closable="false" show-icon />
        </div>

        <!-- 分项评分 -->
        <div class="score-details-section">
          <h2>📈 各维度评分</h2>
          <el-row :gutter="20">
            <el-col :span="12">
              <!-- 雷达图 -->
              <div ref="radarChartRef" class="chart-container"></div>
            </el-col>
            <el-col :span="12">
              <!-- 步骤分数列表 -->
              <el-timeline>
                <el-timeline-item
                  v-for="(step, index) in reportData.step_scores"
                  :key="index"
                  :timestamp="`步骤 ${index + 1}`"
                  placement="top"
                  :color="getStepColor(step.score)"
                >
                  <el-card shadow="hover">
                    <div class="step-item">
                      <span class="step-name">{{ step.step_name }}</span>
                      <el-tag :type="getScoreTagType(step.score)">{{ step.score }}分</el-tag>
                    </div>
                    <p v-if="step.feedback" class="step-feedback">{{ step.feedback }}</p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-col>
          </el-row>
        </div>

        <!-- 问题列表 -->
        <div v-if="reportData.problems && reportData.problems.length > 0" class="problems-section">
          <h2>⚠️ 需要改进的地方</h2>
          <ul class="problem-list">
            <li v-for="(problem, index) in reportData.problems" :key="index">
              <el-icon class="problem-icon"><Warning /></el-icon>
              {{ problem }}
            </li>
          </ul>
        </div>

        <!-- 改进建议 -->
        <div v-if="reportData.suggestions && reportData.suggestions.length > 0" class="suggestions-section">
          <h2>✅ 改进建议</h2>
          <el-collapse>
            <el-collapse-item
              v-for="(suggestion, index) in reportData.suggestions"
              :key="index"
              :title="`建议 ${index + 1}`"
            >
              {{ suggestion }}
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { getTrainingDetail } from '@/api/training'
import * as echarts from 'echarts'

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
  if (score >= 90) return 'success'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 获取步骤颜色
const getStepColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 加载报告数据
const loadReportData = async () => {
  loading.value = true
  try {
    const res = await getTrainingDetail(reportData.training_id)
    
    // 解析数据
    reportData.total_score = res.total_score || 0
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
    
    // 解析步骤分数
    if (res.step_scores) {
      reportData.step_scores = res.step_scores
    }
    
    // 从反馈中生成问题列表和建议（简化处理）
    if (res.feedback) {
      // TODO: 使用真实的 AI 反馈生成器结果
      reportData.problems = ['部分动作不够规范，需要加强练习']
      reportData.suggestions = [
        '注意保持正确的姿势',
        '加强对灭火器操作步骤的记忆',
        '多进行模拟训练'
      ]
    }
    
    // 渲染图表
    renderRadarChart()
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载报告失败')
  } finally {
    loading.value = false
  }
}

// 渲染雷达图
const renderRadarChart = () => {
  if (!radarChartRef.value) return
  
  // 初始化图表
  radarChart = echarts.init(radarChartRef.value)
  
  // 准备数据
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
  padding: 20px;
}

.report-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-content {
  padding: 10px;
}

.total-score-section {
  margin-bottom: 30px;
}

.feedback-section {
  margin-bottom: 30px;
}

.feedback-section h2 {
  margin-bottom: 15px;
  color: #303133;
}

.score-details-section {
  margin-bottom: 30px;
}

.score-details-section h2 {
  margin-bottom: 20px;
  color: #303133;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.step-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.step-name {
  font-weight: 500;
  color: #303133;
}

.step-feedback {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}

.problems-section {
  margin-bottom: 30px;
}

.problems-section h2 {
  margin-bottom: 15px;
  color: #F56C6C;
}

.problem-list {
  list-style: none;
  padding: 0;
}

.problem-list li {
  padding: 10px;
  background: #FEF0F0;
  border-radius: 4px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  color: #F56C6C;
}

.problem-icon {
  margin-right: 10px;
  font-size: 18px;
}

.suggestions-section h2 {
  margin-bottom: 15px;
  color: #67C23A;
}
</style>
