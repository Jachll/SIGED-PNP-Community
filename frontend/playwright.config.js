import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const backendDir = path.resolve(repoRoot, "backend");

export default defineConfig({
  testDir: path.resolve(__dirname, "e2e"),
  globalSetup: path.resolve(__dirname, "e2e", "global-setup.js"),
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: {
    timeout: 15_000
  },
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    channel: process.env.PW_CHANNEL || "chrome",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  },
  webServer: [
    {
      command: `${path.join("..", "backend", ".venv", "Scripts", "uvicorn.exe")} app.main:app --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/health",
      cwd: backendDir,
      reuseExistingServer: true,
      timeout: 120_000
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173",
      cwd: __dirname,
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_BASE_URL: "http://127.0.0.1:8000"
      }
    }
  ]
});
