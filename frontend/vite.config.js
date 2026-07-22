import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      // Forward all /api/* requests to the FastAPI backend.
      // All backend routes use the /api/v1 prefix.
      '/api': 'http://localhost:8000',
    },
  },
})

