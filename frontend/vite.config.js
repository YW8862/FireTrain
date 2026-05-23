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
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    allowedHosts: [
      'firetrain.cn',
      'www.firetrain.cn'
    ],
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
        ws: true,
        xfwd: true
      },
      '/health': {
        target: backendTarget,
        changeOrigin: true,
        xfwd: true
      },
      '/docs': {
        target: backendTarget,
        changeOrigin: true,
        xfwd: true
      },
      '/redoc': {
        target: backendTarget,
        changeOrigin: true,
        xfwd: true
      },
      '/openapi.json': {
        target: backendTarget,
        changeOrigin: true,
        xfwd: true
      }
    }
  },
  
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    sourcemap: true
  }
})
