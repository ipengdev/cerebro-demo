import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(async ({ mode }) => {
  const { default: frappeui } = await import('frappe-ui/vite')

  return {
    plugins: [
      frappeui({
        frappeProxy: true,
        lucideIcons: true,
        jinjaBootData: true,
        buildConfig: {
          indexHtmlPath: '../e_tax/www/e-tax.html',
          emptyOutDir: true,
          sourcemap: true,
        },
      }),
      vue(),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    optimizeDeps: {
      include: ['feather-icons', 'tailwind.config.js'],
    },
    server: {
      fs: { allow: [path.resolve(__dirname, '..')] },
    },
  }
})
