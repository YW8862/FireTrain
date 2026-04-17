<template>
  <div class="auth-page">
    <div class="auth-panel">
      <div class="auth-side">
        <div class="auth-badge">账号注册</div>
        <h1>创建训练账号</h1>
        <p class="auth-side-text">
          注册后可进入灭火器实操训练页面，查看测评结果、训练统计和个人记录。
        </p>
        <div class="safety-note">
          <strong>注册提醒</strong>
          <span>请使用真实可识别的训练账号名称，便于后续记录查询和管理员分配训练视频。</span>
        </div>
      </div>

      <el-card class="register-card section-card">
        <div class="auth-card-header">
          <p class="eyebrow">新建账号</p>
          <h2 class="register-title">注册训练账号</h2>
          <p class="register-subtitle">填写基础信息后即可返回登录页进入系统。</p>
        </div>

        <el-form :model="form" :rules="rules" ref="registerFormRef" label-position="top" @keyup.enter="handleRegister">
          <el-form-item label="训练账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入训练账号" clearable @keyup.enter="focusEmail" />
          </el-form-item>

          <el-form-item label="联系邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入联系邮箱" clearable @keyup.enter="focusPassword" />
          </el-form-item>

          <el-form-item label="登录密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入登录密码" show-password @keyup.enter="focusConfirmPassword" ref="passwordInput" />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入登录密码" show-password @keyup.enter="handleRegister" ref="confirmPasswordInput" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleRegister" :loading="loading" class="submit-btn">
              注册训练账号
            </el-button>
          </el-form-item>
        </el-form>

        <div class="auth-links">
          <span>已有账号？</span>
          <router-link to="/login">返回登录</router-link>
        </div>

        <div class="auth-footer-tip">
          注册成功后将跳转登录页，后续可根据账号角色进入用户端或管理端。
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api/user'

const router = useRouter()
const registerFormRef = ref(null)
const passwordInput = ref(null)
const confirmPasswordInput = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度 3-20 位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  // 防止重复提交
  if (loading.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        console.log('开始调用注册 API...')
        console.log('请求数据:', form)
        
        // 调用注册 API
        await register({
          username: form.username,
          email: form.email,
          password: form.password,
          phone: null  // 手机号暂时不传
        })
        
        console.log('注册成功!')
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } catch (error) {
        console.error('注册失败详情:', error)
        console.error('错误响应:', error.response)
        console.error('错误消息:', error.message)
        
        let errorMsg = '注册失败'
        if (error.response) {
          // 服务器返回了响应
          errorMsg = error.response.data?.detail || `服务器错误：${error.response.status}`
        } else if (error.request) {
          // 请求已发送但没有收到响应
          errorMsg = '无法连接到服务器，请检查后端服务是否启动'
        } else {
          // 其他错误
          errorMsg = error.message || '未知错误'
        }
        
        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}

// 输入框之间的 Enter 键聚焦切换
const focusEmail = () => {
  const emailInput = registerFormRef.value?.fields?.find(f => f.prop === 'email')?.input
  if (emailInput) {
    emailInput.focus()
  }
}

const focusPassword = () => {
  if (passwordInput.value) {
    passwordInput.value.focus()
  }
}

const focusConfirmPassword = () => {
  if (confirmPasswordInput.value) {
    confirmPasswordInput.value.focus()
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.06), rgba(30, 64, 175, 0)),
    var(--ft-color-page-bg);
}

.auth-panel {
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: 1fr 0.95fr;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid var(--ft-color-border);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
  background: var(--ft-color-surface);
}

.auth-side {
  padding: 48px;
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.04), rgba(16, 185, 129, 0.05)),
    #f8fafc;
  border-right: 1px solid var(--ft-color-border);
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 100px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(30, 64, 175, 0.12);
  color: var(--ft-color-primary);
  font-weight: 700;
}

.auth-side h1 {
  margin: 22px 0 12px;
  font-size: 32px;
}

.auth-side-text {
  max-width: 420px;
  color: var(--ft-color-text-secondary);
  line-height: 1.8;
}

.safety-note {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 12px;
  background: #f5fbf8;
  border: 1px solid rgba(16, 185, 129, 0.16);
}

.safety-note strong {
  color: var(--ft-color-success);
}

.register-card {
  border: 0;
  box-shadow: none;
  padding: 26px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.auth-card-header {
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--ft-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.register-title {
  margin: 0;
  font-size: 28px;
}

.register-subtitle {
  margin: 8px 0 0;
  color: var(--ft-color-text-tertiary);
}

.submit-btn {
  width: 100%;
  min-height: 42px;
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

.auth-footer-tip {
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--ft-color-surface-muted);
  color: var(--ft-color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .auth-panel {
    grid-template-columns: 1fr;
  }

  .auth-side {
    padding: 28px 24px 20px;
    border-right: 0;
    border-bottom: 1px solid var(--ft-color-border);
  }
}

@media (max-width: 640px) {
  .auth-page {
    padding: 16px;
  }

  .auth-side h1 {
    font-size: 26px;
  }

  .register-card {
    padding: 16px;
  }
}
</style>
