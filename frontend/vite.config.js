import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { resolve, dirname } from 'node:path'
import sirv from 'sirv'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Plugin to serve MkDocs static files from /docs path
function serveMkDocs() {
  return {
    name: 'serve-mkdocs',
    configureServer(server) {
      const siteDir = resolve(__dirname, '../site')
      const serve = sirv(siteDir, { dev: true, single: false })
      server.middlewares.use('/docs', serve)
    }
  }
}

export default defineConfig({
  plugins: [vue(), serveMkDocs()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '3000', 10),
    host: process.env.FRONTEND_HOST !== undefined ? process.env.FRONTEND_HOST : true,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

