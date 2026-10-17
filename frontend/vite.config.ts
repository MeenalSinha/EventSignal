import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Configuration is read from the repository-root .env (shared with the backend).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "VITE_");
  const port = Number(env.VITE_DEV_SERVER_PORT);

  return {
    envDir: "..",
    plugins: [react(), tailwindcss()],
    server: {
      ...(Number.isInteger(port) && port > 0 ? { port } : {}),
      // Used only when VITE_API_BASE_URL is empty (proxy mode); see README.
      ...(env.VITE_PROXY_TARGET
        ? { proxy: { "/api": { target: env.VITE_PROXY_TARGET, changeOrigin: true } } }
        : {}),
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      css: false,
      exclude: ["**/node_modules/**", "**/dist/**", "**/*.live.test.tsx"],
      // Test-only values: tests never read the developer's real .env.
      env: {
        VITE_API_BASE_URL: "http://api.test",
        VITE_REQUEST_TIMEOUT_MS: "2000",
      },
    },
  };
});
