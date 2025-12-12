import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import sirv from 'sirv'

// Plugin to serve MkDocs static files from /docs path
function serveMkDocs() {
  return {
    name: 'serve-mkdocs',
    configureServer(server) {
      // In Docker, site folder is mounted at /site
      const serve = sirv('/site', { dev: true, single: false })
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
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
})

