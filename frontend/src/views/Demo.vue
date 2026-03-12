<template>
  <div class="demo-page">
    <el-container>
      <el-header>
        <h1>🔥 FireTrain 智能消防训练系统</h1>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <!-- 左侧：用户模块 -->
          <el-col :span="12">
            <el-card class="box-card">
              <template #header>
                <div class="card-header">
                  <span>👤 用户登录/注册</span>
                </div>
              </template>
              
              <!-- 登录表单 -->
              <div v-if="showLogin">
                <el-form :model="loginForm" label-width="80px">
                  <el-form-item label="用户名">
                    <el-input v-model="loginForm.username" placeholder="请输入用户名" />
                  </el-form-item>
                  <el-form-item label="密码">
                    <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="handleLogin">登录</el-button>
                    <el-button @click="showLogin = false">去注册</el-button>
                  </el-form-item>
                </el-form>
                
                <div v-if="currentUser" class="user-info">
                  <el-divider />  
                  <h3>✅ 已登录</h3>
                  <p><strong>用户名:</strong> {{ currentUser.username }}</p>
                  <p><strong>邮箱:</strong> {{ currentUser.email }}</p>
                  <p><strong>角色:</strong> {{ currentUser.role }}</p>
                  <el-button type="danger" @click="handleLogout">退出登录</el-button>
                </div>
              </div>
              
              <!-- 注册表单 -->
              <div v-else>
                <el-form :model="registerForm" label-width="80px">
                  <el-form-item label="用户名">
                    <el-input v-model="registerForm.username" placeholder="3-50 个字符" />
                  </el-form-item>
                  <el-form-item label="邮箱">
                    <el-input v-model="registerForm.email" placeholder="example@email.com" />
                  </el-form-item>
                  <el-form-item label="密码">
                    <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" />
                  </el-form-item>
                  <el-form-item label="手机号">
                    <el-input v-model="registerForm.phone" placeholder="可选" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="success" @click="handleRegister">注册</el-button>
                    <el-button @click="showLogin = true">去登录</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-card>
          </el-col>
          
          <!-- 右侧：API 测试状态 -->
          <el-col :span="12">
            <el-card class="box-card">
              <template #header>
                <div class="card-header">
                  <span>📊 API 测试状态</span>
                </div>
              </template>
              
              <el-descriptions title="后端服务状态" :column="1" border>
                <el-descriptions-item label="服务地址">
                  <el-tag :type="backendStatus ? 'success' : 'danger'">
                    {{ backendStatus ? '运行中 ✅' : '未连接 ❌' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="API 文档">
                  <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a>
                </el-descriptions-item>
                <el-descriptions-item label="健康检查">
                  <el-tag :type="healthStatus ? 'success' : 'danger'">
                    {{ healthStatus ? '正常 ✅' : '异常 ❌' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              
              <el-divider />
              
              <div class="api-links">
                <h3>🔗 快速链接</h3>
                <ul>
                  <li><a href="http://localhost:8000/docs" target="_blank">Swagger API 文档</a></li>
                  <li><a href="http://localhost:8000/redoc" target="_blank">ReDoc 文档</a></li>
                  <li><a href="http://localhost:8000/health" target="_blank">健康检查</a></li>
                </ul>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
      
      <el-footer>
        <p>FireTrain v0.1.0 | 阶段 C1 - 用户模块已完成 ✅</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 登录状态
const showLogin = ref(true)
const currentUser = ref(null)

// 后端状态
const backendStatus = ref(false)
const healthStatus = ref(false)

// 登录表单
const loginForm = ref({
  username: '',
  password: ''
})

// 注册表单
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  phone: ''
})

// 检查后端健康状态
const checkHealth = async () => {
  try {
    const response = await fetch('http://localhost:8000/health')
    if (response.ok) {
      healthStatus.value = true
      backendStatus.value = true
    }
  } catch (error) {
    console.error('Backend health check failed:', error)
    healthStatus.value = false
    backendStatus.value = false
  }
}

// 处理登录
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  try {
    const formData = new URLSearchParams()
    formData.append('username', loginForm.value.username)
    formData.append('password', loginForm.value.password)
    
    const response = await fetch('http://localhost:8000/api/user/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
    })
    
    const data = await response.json()
    
    if (response.ok) {
      ElMessage.success('登录成功！')
      currentUser.value = data.user_info
      // 保存 token
      localStorage.setItem('token', data.token)
    } else {
      ElMessage.error(data.detail || '登录失败')
    }
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error('网络错误，请检查后端服务是否启动')
  }
}

// 处理注册
const handleRegister = async () => {
  if (!registerForm.value.username || !registerForm.value.email || !registerForm.value.password) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/user/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(registerForm.value)
    })
    
    const data = await response.json()
    
    if (response.ok) {
      ElMessage.success('注册成功！请登录')
      showLogin.value = true
      // 清空表单
      registerForm.value = {
        username: '',
        email: '',
        password: '',
        phone: ''
      }
    } else {
      ElMessage.error(data.detail || '注册失败')
    }
  } catch (error) {
    console.error('Register error:', error)
    ElMessage.error('网络错误，请检查后端服务是否启动')
  }
}

// 处理登出
const handleLogout = () => {
  currentUser.value = null
  loginForm.value = {
    username: '',
    password: ''
  }
  localStorage.removeItem('token')
  ElMessage.info('已退出登录')
}

// 组件挂载时检查后端状态
onMounted(() => {
  checkHealth()
  // 检查本地存储的 token
  const token = localStorage.getItem('token')
  if (token) {
    ElMessage.info('检测到已保存的登录状态')
  }
})
</script>

<style scoped>
.demo-page {
  width: 100%;
  height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}

.box-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.user-info h3 {
  color: #67C23A;
  margin-bottom: 10px;
}

.user-info p {
  margin: 8px 0;
  color: #606266;
}

.api-links {
  margin-top: 20px;
}

.api-links ul {
  list-style: none;
  padding-left: 0;
}

.api-links li {
  margin: 10px 0;
}

.api-links a {
  color: #409EFF;
  text-decoration: none;
}

.api-links a:hover {
  text-decoration: underline;
}

.el-footer {
  background-color: #545c64;
  color: white;
  text-align: center;
  line-height: 60px;
}
</style>
