import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import http from 'http';
import { spawn } from 'child_process';
import { defineConfig } from 'vite';

let pythonProc: any = null;
function ensurePythonServer() {
  if (pythonProc) return;
  // Check if port 8765 is already responding
  const req = http.get('http://127.0.0.1:8765/api/state', (res) => {
    res.resume();
  });
  req.on('error', () => {
    pythonProc = spawn('python3', ['/app/applet/gpo_sim_agent/run_app.py'], {
      cwd: '/app/applet/gpo_sim_agent',
      stdio: 'inherit',
    });
    pythonProc.on('exit', () => {
      pythonProc = null;
    });
  });
}

function pythonProxyPlugin() {
  return {
    name: 'python-proxy-plugin',
    configureServer(server: any) {
      ensurePythonServer();
      server.middlewares.use((req: any, res: any, next: any) => {
        if (req.url === '/app-frame' || req.url === '/app-frame/') {
          const proxyReq = http.request(
            {
              hostname: '127.0.0.1',
              port: 8765,
              path: '/',
              method: req.method,
              headers: {
                ...req.headers,
                host: '127.0.0.1:8765',
              },
            },
            (proxyRes) => {
              res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
              proxyRes.pipe(res);
            }
          );
          proxyReq.on('error', (err) => {
            res.statusCode = 502;
            res.end('Python App starting on port 8765... ' + err.message);
          });
          req.pipe(proxyReq);
          return;
        }
        next();
      });
    },
  };
}

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss(), pythonProxyPlugin()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify—file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8765',
          changeOrigin: true,
        },
        '/assets': {
          target: 'http://127.0.0.1:8765',
          changeOrigin: true,
        },
      },
    },
  };
});
