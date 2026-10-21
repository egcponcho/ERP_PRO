import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    port: 5173,
    // La API corre en el puerto 8000 (uvicorn); en producción la sirve el mismo servidor
    proxy: { '/api': 'http://localhost:8000' },
  },
})
