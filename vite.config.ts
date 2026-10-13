import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: { rollupOptions: { input: { app: resolve(process.cwd(), 'index.html'), projectBrief: resolve(process.cwd(), 'seon-project-brief.html') } } },
})
