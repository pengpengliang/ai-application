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
      // '/api': {
      //   target: 'https://www.news.cn',
      //   changeOrigin: true,
      //   rewrite: (path) => path.replace(/^\/api/, ''),
      // }
    },
  },
})