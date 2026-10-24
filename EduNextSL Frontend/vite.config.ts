import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin API in development, so the HttpOnly refresh cookie just works.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  build: {
    // Django serves this folder (FRONTEND_DIST_DIR); see backend/README.md.
    outDir: "../backend/frontend_dist",
    emptyOutDir: true,
  },
});
