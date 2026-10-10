/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  // tanstackRouter must come before react()
  plugins: [tanstackRouter({ target: 'react' }), react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // Same-origin API in dev (ADR-002)
    proxy: { '/api': 'http://localhost:8000' },
    // Tests import the backend fixtures (src/test/mockWikiApi.ts)
    fs: { allow: ['..'] },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
