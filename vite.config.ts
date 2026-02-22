import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  server: {
    proxy: {
      '/news': {
        target: 'https://www.news.cn/',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/news/, ''),
      },
      '/python-server': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/python-server/, ''),
      },
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true
      },
      '/docServe': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/docServe/, ''),
      }
    },
  },
})