<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">FireTrain 消防技能训练系统</h2>
      <p class="register-subtitle">用户注册</p>
      
      <el-form :model="form" :rules="rules" ref="registerFormRef" label-width="80px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" clearable />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" clearable />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" style="width: 100%">
            注册
          </el-button>
        </el-form-item>
        
        <div class="register-links">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api/user'

const router = useRouter()
const registerFormRef = ref(null)
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
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 450px;
  padding: 20px;
}

.register-title {
  text-align: center;
  color: #303133;
  margin-bottom: 10px;
  font-size: 24px;
}

.register-subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
  font-size: 16px;
}

.register-links {
  text-align: center;
  margin-top: 15px;
  color: #909399;
}

.register-links a {
  color: #409EFF;
  margin-left: 5px;
  text-decoration: none;
}
</style>
