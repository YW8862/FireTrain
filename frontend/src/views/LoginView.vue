<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">FireTrain 消防技能训练系统</h2>
      <p class="login-subtitle">用户登录</p>
      
      <el-form :model="form" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" clearable />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
        
        <div class="login-links">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
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
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(form)
        userStore.setToken(res.token)
        userStore.setUserInfo(res.user_info)
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        console.error('登录失败:', error)
        
        // 根据错误类型给出不同提示
        let errorMsg = '登录失败'
        
        // 优先使用 request.js 中设置的自定义错误信息
        if (error.customMessage) {
          errorMsg = error.customMessage
          if (error.suggestion) {
            console.log('建议:', error.suggestion)
          }
        } else if (error.code === 'ERR_CERT_AUTHORITY_INVALID' || error.message?.includes('certificate')) {
          errorMsg = 'SSL 证书错误，请检查服务器配置或使用 HTTP 连接'
        } else if (!navigator.onLine) {
          errorMsg = '网络连接已断开，请检查网络设置'
        } else if (error.response) {
          // 服务器返回了响应
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
          // 请求已发送但没有收到响应
          errorMsg = '无法连接到服务器，请检查：\n1. 后端服务是否启动\n2. 网络连接是否正常\n3. 服务器地址是否正确'
        } else {
          // 其他错误
          errorMsg = error.message || '未知错误，请稍后重试'
        }
        
        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  padding: 20px;
}

.login-title {
  text-align: center;
  color: #303133;
  margin-bottom: 10px;
  font-size: 24px;
}

.login-subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
  font-size: 16px;
}

.login-links {
  text-align: center;
  margin-top: 15px;
  color: #909399;
}

.login-links a {
  color: #409EFF;
  margin-left: 5px;
  text-decoration: none;
}
</style>
