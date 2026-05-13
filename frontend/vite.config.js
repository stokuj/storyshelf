import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'health-check',
      configureServer(server) {
        server.middlewares.use('/health', (_req, res) => {
          res.statusCode = 200
          res.setHeader('Content-Type', 'text/plain')
          res.end('OK')
        })
      },
    },
  ],
  build: {
    sourcemap: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/static': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
