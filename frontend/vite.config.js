import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import fs from 'fs'

const backendTarget = 'http://localhost:8000'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,  // 强制使用指定端口，如果被占用则报错
    https: {
      key: fs.readFileSync('../certs/key.pem'),
      cert: fs.readFileSync('../certs/cert.pem')
    },
    proxy: {
      '/api': {
        target: backendTarget,  // 统一由前端 HTTPS 入口代理到内部 HTTP 后端
        changeOrigin: true,
        secure: false,
        ws: true
      },
      '/health': {
        target: backendTarget,
        changeOrigin: true
      },
      '/docs': {
        target: backendTarget,
        changeOrigin: true
      },
      '/redoc': {
        target: backendTarget,
        changeOrigin: true
      },
      '/openapi.json': {
        target: backendTarget,
        changeOrigin: true
      }
    },
    // 允许外部访问
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '117.72.44.96'
    ]
  },
  
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    sourcemap: true
  }
})
