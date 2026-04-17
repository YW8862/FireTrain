<template>
  <div class="auth-page">
    <el-card class="login-card section-card">
      <div class="auth-card-header">
        <div class="login-title">智能消防训练评测系统</div>
        <!-- <h1 class="login-title">登录训练系统</h1> -->
        <p class="login-subtitle">输入账号和密码即可进入系统。</p>
      </div>

      <el-form :model="form" :rules="rules" ref="loginFormRef" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="训练账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入训练账号" clearable @keyup.enter="focusPassword" />
        </el-form-item>

        <el-form-item label="登录密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入登录密码" show-password @keyup.enter="handleLogin" ref="passwordInput" />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
        </div>

        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" class="submit-btn">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-links">
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
    </el-card>
  </div>
 </template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/user'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const passwordInput = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  if (loading.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(form)
        userStore.setToken(res.token)
        userStore.setUserInfo(res.user_info)
        ElMessage.success('登录成功')

        const role = res.user_info?.role || 'user'

        if (role === 'admin' || role === 'root') {
          router.push('/admin/dashboard')
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('登录失败:', error)

        let errorMsg = '登录失败'

        if (error.customMessage) {
          errorMsg = error.customMessage
        } else if (error.code === 'ERR_CERT_AUTHORITY_INVALID' || error.message?.includes('certificate')) {
          errorMsg = 'SSL 证书错误，请检查服务器配置或使用 HTTP 连接'
        } else if (!navigator.onLine) {
          errorMsg = '网络连接已断开，请检查网络设置'
        } else if (error.response) {
          const status = error.response.status
          switch (status) {
            case 401:
              errorMsg = '账号或密码错误，请重新输入'
              break
            case 403:
              errorMsg = '访问被拒绝，请联系管理员'
              break
            case 404:
              errorMsg = '登录接口不存在'
              break
            case 500:
              errorMsg = '服务器错误，请稍后重试'
              break
            default:
              errorMsg = error.response.data?.detail || `登录失败 (${status})`
          }
        } else if (error.request) {
          errorMsg = '无法连接到服务器，请检查后端服务、网络连接和服务器地址'
        } else {
          errorMsg = error.message || '未知错误，请稍后重试'
        }

        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}

const focusPassword = () => {
  if (passwordInput.value) {
    passwordInput.value.focus()
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background:
    radial-gradient(circle at top, rgba(30, 64, 175, 0.08), transparent 30%),
    var(--ft-color-page-bg);
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(30, 64, 175, 0.12);
  color: var(--ft-color-primary);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.login-card {
  width: min(420px, 100%);
  padding: 28px 24px 22px;
  border-radius: 18px;
}

.auth-card-header {
  margin-bottom: 14px;
  text-align: center;
}

.login-title {
  margin: 16px 0 0;
  color: var(--ft-color-primary);
  font-size: 32px;
  font-weight: 600;
}

.login-subtitle {
  margin: 10px 0 0;
  color: var(--ft-color-text-tertiary);
}

.login-options {
  display: flex;
  align-items: center;
  margin: 2px 0 12px;
}

.submit-btn {
  width: 100%;
  min-height: 44px;
}

.auth-links {
  margin-top: 8px;
  text-align: center;
  color: var(--ft-color-text-tertiary);
}

.auth-links a {
  color: var(--ft-color-primary);
  margin-left: 6px;
  text-decoration: none;
  font-weight: 600;
}

@media (max-width: 640px) {
  .login-card {
    padding: 22px 16px 18px;
  }

  .login-title {
    font-size: 26px;
  }
}
</style>
