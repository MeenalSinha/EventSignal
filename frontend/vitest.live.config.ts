import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Live integration tests: the real React app against a real running backend.
// Orchestrated by scripts/integration_test.py, which supplies the URLs below.
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.live.test.tsx"],
    css: false,
  },
});
