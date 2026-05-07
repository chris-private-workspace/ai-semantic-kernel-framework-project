import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

// V2 frontend dev server config.
// Port 3007 chosen to avoid collision with archived V1 frontend (3005).
// Backend dev server runs on 8000 (Sprint 57.6 US-1 R1 closeout — fixed from
// stale 8001 stub-port reference; closes 57.5 D-21 port drift).
// Vitest config added Sprint 57.1 (per Day 0 D11 — frontend had no Vitest before).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 3007,
    strictPort: true,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    target: "es2022",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/unit/setup.ts"],
    include: ["tests/unit/**/*.{test,spec}.{ts,tsx}"],
    exclude: ["tests/e2e/**", "node_modules/**"],
  },
});
