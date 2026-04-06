import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import fs from 'fs'

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
        target: 'http://localhost:8000',  // 后端 HTTP 地址
        changeOrigin: true,
        secure: false,  // 允许自签名证书
        ws: true
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
