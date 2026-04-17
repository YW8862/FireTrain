<template>
  <div class="app-page home-page">
    <NavBar />
    <div class="app-shell home-shell">
      <section class="hero-section">
        <div class="hero-copy">
          <div class="hero-meta">
            <img :src="flameSymbol" alt="" class="meta-icon" />
            <span>消防实操训练</span>
          </div>

          <h1 class="hero-title">智能消防实操训练测评系统</h1>
          <p class="hero-subtitle">
            聚焦训练本身。进入实操训练，完成动作记录，查看测评结果。
          </p>

          <div class="hero-actions">
            <el-button type="primary" size="large" class="hero-primary" @click="goToTraining">
              <el-icon><VideoPlay /></el-icon>
              开始训练
            </el-button>
            <el-button size="large" @click="viewHistory">
              <el-icon><Document /></el-icon>
              训练记录
            </el-button>
            <el-button size="large" @click="goToStats">
              <el-icon><DataLine /></el-icon>
              训练统计
            </el-button>
          </div>

          <div class="hero-note">
            <el-icon><WarningFilled /></el-icon>
            <span>训练前请确认设备、场地与人员站位安全，保持完整入镜。</span>
          </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
          <div class="visual-ring"></div>
          <img :src="fireExtinguisherSymbol" alt="" class="visual-extinguisher" />
          <img :src="flameSymbol" alt="" class="visual-flame" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { 
  DataLine,
  VideoPlay,
  Document,
  WarningFilled
} from '@element-plus/icons-vue'
import NavBar from '@/components/NavBar.vue'
import fireExtinguisherSymbol from '@/assets/illustrations/fire-extinguisher-symbol.svg'
import flameSymbol from '@/assets/illustrations/flame-symbol.svg'

const router = useRouter()

// 跳转到训练页面
const goToTraining = () => {
  router.push('/training')
}

// 查看历史记录
const viewHistory = () => {
  router.push('/history')
}

const goToStats = () => {
  router.push('/stats')
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

.home-shell {
  min-height: calc(100vh - 82px);
  display: flex;
  align-items: stretch;
}

.hero-section {
  position: relative;
  width: 100%;
  min-height: calc(100vh - 130px);
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 520px);
  gap: 32px;
  align-items: center;
  padding: 32px 8px 20px;
}

.hero-copy {
  max-width: 720px;
}

.hero-meta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(22, 50, 125, 0.08);
  border: 1px solid rgba(22, 50, 125, 0.12);
  color: var(--ft-color-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.meta-icon {
  width: 18px;
  height: 18px;
}

.hero-title {
  margin: 20px 0 0;
  font-size: 60px;
  line-height: 1.08;
  letter-spacing: -0.03em;
  color: var(--ft-color-text-primary);
  max-width: 760px;
}

.hero-subtitle {
  margin: 22px 0 0;
  max-width: 580px;
  color: var(--ft-color-text-secondary);
  line-height: 1.9;
  font-size: 18px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 34px;
}

.hero-primary {
  min-width: 160px;
}

.hero-note {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 28px;
  padding: 14px 16px;
  width: fit-content;
  max-width: 100%;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid var(--ft-color-border);
  box-shadow: var(--ft-shadow-sm);
  color: var(--ft-color-text-secondary);
}

.hero-visual {
  position: relative;
  min-height: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-ring {
  position: absolute;
  width: min(32vw, 460px);
  height: min(32vw, 460px);
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(217, 33, 33, 0.12) 0%, rgba(245, 158, 11, 0.08) 45%, rgba(255, 255, 255, 0) 72%);
}

.visual-extinguisher {
  position: relative;
  width: min(26vw, 340px);
  max-width: 100%;
  filter: drop-shadow(0 20px 40px rgba(15, 23, 42, 0.12));
  z-index: 2;
}

.visual-flame {
  position: absolute;
  right: 4%;
  top: 10%;
  width: min(12vw, 120px);
  opacity: 0.92;
  filter: drop-shadow(0 12px 24px rgba(217, 33, 33, 0.18));
}

@media (max-width: 1024px) {
  .hero-section {
    grid-template-columns: 1fr;
    min-height: auto;
    padding-top: 24px;
  }

  .hero-title {
    font-size: 52px;
  }

  .hero-visual {
    min-height: 360px;
    order: -1;
  }

  .visual-ring {
    width: 320px;
    height: 320px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 38px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-note {
    width: 100%;
    align-items: flex-start;
  }

  .hero-visual {
    min-height: 280px;
  }

  .visual-extinguisher {
    width: 200px;
  }

  .visual-flame {
    width: 72px;
  }
}
</style>
