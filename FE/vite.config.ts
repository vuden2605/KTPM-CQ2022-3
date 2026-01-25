import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Fix sockjs-client "global is not defined" error
    global: 'globalThis',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'http://localhost:8083',
        ws: true,
        changeOrigin: true,
      }
    },
  },
})
