import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_')

  return {
    plugins: [react()],
    server: {
      strictPort: true,
      watch: {
        usePolling: env.VITE_USE_POLLING === 'true',
      },
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8001',
          changeOrigin: false,
        },
      },
    },
  }
})
