import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'
import { copyFileSync, mkdirSync } from 'node:fs'

const copyLegacyRuntimeFiles = {
  name: 'copy-legacy-runtime-files',
  apply: 'build',
  closeBundle() {
    const outputDirectory = resolve(process.cwd(), 'dist')
    mkdirSync(outputDirectory, { recursive: true })
    for (const file of ['smarttime-config.js', 'auth.js', 'student-dashboard.js', 'admin-change-password.js']) {
      copyFileSync(resolve(process.cwd(), file), resolve(outputDirectory, file))
    }
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), copyLegacyRuntimeFiles],
  cacheDir: "backend/academic_tms/.vite-cache",
  build: {
    emptyOutDir: false,
    rollupOptions: {
      input: {
        home: resolve(process.cwd(), 'Index.html'),
        legacyHome: resolve(process.cwd(), 'legacy-index.html'),
        login: resolve(process.cwd(), 'login.html'),
        register: resolve(process.cwd(), 'register.html'),
        admin: resolve(process.cwd(), 'admin.html'),
        faculty: resolve(process.cwd(), 'faculty-dashboard.html'),
        student: resolve(process.cwd(), 'student-dashboard.html'),
        forgotPassword: resolve(process.cwd(), 'forgot-password.html'),
      },
    },
  },
})
