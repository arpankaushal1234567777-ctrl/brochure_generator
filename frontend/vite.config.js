import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Local dev hits your running backend (uvicorn). Override with VITE_API_PROXY_TARGET if needed.
const API_TARGET = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false,
      }
    }
  }
})