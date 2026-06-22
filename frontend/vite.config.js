import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // In local dev, /api/* → Railway backend (mirrors the Vercel rewrite)
      '/api': {
        target: 'https://brochuregenerator-production-2f19.up.railway.app',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: true,
      }
    }
  }
})