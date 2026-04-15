import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const src = path.resolve(__dirname, '../../employee_self_service/public/frontend/index.html')
const dest = path.resolve(__dirname, '../../employee_self_service/www/ess.html')

let html = fs.readFileSync(src, 'utf8')

// 1. Set data-theme directly on <html> tag via Jinja (present from first byte)
html = html.replace(
  '<html class="h-full" lang="en">',
  `{%- set _theme = boot.desk_theme or "light" -%}
{%- if _theme == "automatic" -%}
  <html class="h-full" lang="en">
{%- else -%}
  <html class="h-full" lang="en" data-theme="{{ _theme }}">
{%- endif -%}`
)

// 2. Extract the boot script from <body> and move it into <head> before the module script
const bootScriptRegex = /(\s*<script>\s*\{%\s*for key in boot[\s\S]*?\{%\s*endfor\s*%\}\s*<\/script>)/
const bootMatch = html.match(bootScriptRegex)

if (bootMatch) {
  // Remove from body
  html = html.replace(bootMatch[0], '')

  // Build combined boot + theme script block for <head>
  const headScripts = `
    <script>
      {% for key in boot %}
      window["{{ key }}"] = {{ boot[key] | tojson }};
      {% endfor %}
    </script>
    <script>
      (function() {
        var t = window.desk_theme || 'light';
        if (t === 'automatic') {
          t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        document.documentElement.setAttribute('data-theme', t);
      })();
    </script>`

  // Insert before the first <script type="module"> so boot vars are set before app runs
  html = html.replace(
    /(\s*<script type="module")/,
    headScripts + '\n   $1'
  )
}

fs.writeFileSync(dest, html)
console.log('Copied and patched ess.html with theme script')
