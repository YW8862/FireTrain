<template>
  <el-card class="demo-login-card section-card">
    <div class="demo-login-header">
      <div>
        <h3 class="demo-login-title">演示模式快捷登录</h3>
        <p class="demo-login-subtitle">
          仅用于答辩与演示环境。点击下方账号可直接体验不同角色视图。
        </p>
      </div>
      <el-tag type="warning" effect="light">Demo</el-tag>
    </div>

    <div class="demo-account-list">
      <button
        v-for="account in accounts"
        :key="account.key"
        type="button"
        class="demo-account-item"
        :disabled="loading"
        @click="$emit('quick-login', account)"
      >
        <div class="demo-account-main">
          <div class="demo-account-meta">
            <span class="demo-account-name">{{ account.username }}</span>
            <el-tag size="small" :type="getRoleTagType(account.role)">
              {{ getRoleLabel(account.role) }}
            </el-tag>
          </div>
          <div class="demo-account-label">{{ account.label }}</div>
          <div class="demo-account-desc">{{ account.description }}</div>
        </div>
        <div class="demo-account-action">快捷登录</div>
      </button>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  accounts: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['quick-login'])

const getRoleLabel = (role) => ({
  student: '用户',
  admin: '管理员',
  root: 'Root'
}[role] || role)

const getRoleTagType = (role) => ({
  student: 'info',
  admin: 'warning',
  root: 'danger'
}[role] || 'info')
</script>

<style scoped>
.demo-login-card {
  width: 100%;
  border-radius: 18px;
}

:deep(.el-card__body) {
  padding: 18px;
}

.demo-login-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.demo-login-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ft-color-text-primary);
}

.demo-login-subtitle {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ft-color-text-tertiary);
}

.demo-account-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.demo-account-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.demo-account-item:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(30, 64, 175, 0.24);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.demo-account-item:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.demo-account-main {
  flex: 1;
  min-width: 0;
}

.demo-account-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.demo-account-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--ft-color-text-primary);
}

.demo-account-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ft-color-primary);
  font-weight: 600;
}

.demo-account-desc {
  margin-top: 4px;
  font-size: 11px;
  color: var(--ft-color-text-tertiary);
}

.demo-account-action {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--ft-color-primary);
}
</style>
