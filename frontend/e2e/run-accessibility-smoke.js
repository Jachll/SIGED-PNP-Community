import { execFileSync, spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendDir, "..");
const backendDir = path.resolve(repoRoot, "backend");
const pythonExecutable = path.resolve(backendDir, ".venv", "Scripts", "python.exe");
const uvicornExecutable = path.resolve(backendDir, ".venv", "Scripts", "uvicorn.exe");
const seedScript = path.resolve(repoRoot, "scripts", "seed_validation_users.py");
const chromeCandidates = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"
];
const backendUrl = "http://127.0.0.1:8000";
const frontendUrl = "http://127.0.0.1:5173";

function getChromeExecutable() {
  const executable = chromeCandidates.find((candidate) => fs.existsSync(candidate));
  if (!executable) {
    throw new Error("No se encontro Chrome/Edge instalado para la validacion de accesibilidad.");
  }
  return executable;
}

function readValidationPassword() {
  const envPath = path.resolve(backendDir, ".env");
  if (!fs.existsSync(envPath)) {
    return "Siged1234!";
  }

  const rawEnv = fs.readFileSync(envPath, "utf8");
  const passwordLine = rawEnv
    .split(/\r?\n/u)
    .find((line) => line.trim().startsWith("SIGED_VALIDATION_PASSWORD="));

  if (!passwordLine) {
    return "Siged1234!";
  }

  const [, rawValue = ""] = passwordLine.split("=", 2);
  return rawValue.trim().replace(/^"|"$/gu, "") || "Siged1234!";
}

async function waitForHttpOk(url, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return true;
      }
    } catch {
      // keep polling
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error(`Timeout esperando ${label}: ${url}`);
}

function spawnDetached(command, args, options = {}) {
  return spawn(command, args, {
    cwd: options.cwd,
    env: options.env,
    stdio: "ignore",
    windowsHide: true,
    detached: true
  });
}

function stopProcessTree(child) {
  if (!child?.pid) {
    return;
  }

  spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
    stdio: "ignore",
    windowsHide: true
  });
}

async function ensureBackend(startedProcesses) {
  try {
    await waitForHttpOk(`${backendUrl}/health`, 2_000, "backend existente");
    return;
  } catch {
    if (!fs.existsSync(uvicornExecutable)) {
      throw new Error(`No se encontro uvicorn en ${uvicornExecutable}`);
    }

    const backendProcess = spawnDetached(
      uvicornExecutable,
      ["app.main:app", "--host", "127.0.0.1", "--port", "8000"],
      { cwd: backendDir, env: process.env }
    );
    startedProcesses.push(backendProcess);
    backendProcess.unref();
    await waitForHttpOk(`${backendUrl}/health`, 120_000, "backend");
  }
}

async function ensureFrontend(startedProcesses) {
  try {
    await waitForHttpOk(frontendUrl, 2_000, "frontend existente");
    return;
  } catch {
    const frontendProcess = spawnDetached(
      "npm.cmd",
      ["run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
      {
        cwd: frontendDir,
        env: {
          ...process.env,
          VITE_API_BASE_URL: backendUrl
        }
      }
    );
    startedProcesses.push(frontendProcess);
    frontendProcess.unref();
    await waitForHttpOk(frontendUrl, 120_000, "frontend");
  }
}

function seedValidationUsers() {
  if (!fs.existsSync(pythonExecutable)) {
    throw new Error(`No se encontro el Python del backend para sembrar usuarios QA: ${pythonExecutable}`);
  }

  execFileSync(pythonExecutable, [seedScript], {
    cwd: repoRoot,
    stdio: "inherit"
  });
}

async function launchBrowserOverCdp(startedProcesses) {
  const chromeExecutable = getChromeExecutable();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "siged-a11y-"));
  const debugPort = 9723 + Math.floor(Math.random() * 300);
  const chromeDebugUrl = `http://127.0.0.1:${debugPort}`;

  const chromeProcess = spawnDetached(
    chromeExecutable,
    [
      "--headless=new",
      "--disable-gpu",
      "--no-sandbox",
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${userDataDir}`,
      "about:blank"
    ],
    { env: process.env }
  );
  startedProcesses.push(chromeProcess);
  chromeProcess.unref();

  await waitForHttpOk(`${chromeDebugUrl}/json/version`, 30_000, "Chrome CDP");
  return chromium.connectOverCDP(chromeDebugUrl);
}

async function login(page, username, password) {
  await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
  await page.locator('[data-testid="login-username"]').waitFor({
    state: "visible",
    timeout: 60_000
  });
  await page.locator('[data-testid="login-username"]').fill(username);
  await page.locator('[data-testid="login-password"]').fill(password);
  await page.locator('[data-testid="login-submit"]').click();
  await page.locator('[data-testid="tab-dashboard-operacional"]').waitFor({
    state: "visible",
    timeout: 60_000
  });
}

async function assertLoginAccessibility(page) {
  if ((await page.title()) !== "SIGED-PNP - ETAPA 2") {
    throw new Error(`Titulo inesperado en login: ${await page.title()}`);
  }

  const htmlLang = await page.locator("html").getAttribute("lang");
  if (htmlLang !== "es") {
    throw new Error(`El documento debe declarar lang=es y hoy devuelve ${htmlLang ?? "null"}.`);
  }

  await page.getByRole("main").waitFor({ state: "visible", timeout: 30_000 });
  await page.getByRole("heading", { name: "Ingreso operativo al frontend" }).waitFor({
    state: "visible",
    timeout: 30_000
  });
  await page.getByLabel("Usuario").waitFor({ state: "visible", timeout: 30_000 });
  await page.getByLabel("Contrasena").waitFor({ state: "visible", timeout: 30_000 });
  await page.getByRole("button", { name: "Entrar" }).waitFor({ state: "visible", timeout: 30_000 });
}

async function assertMainShellAccessibility(page) {
  await page.locator("#app-main").waitFor({ state: "visible", timeout: 30_000 });
  await page.getByRole("navigation", { name: "Vistas principales" }).waitFor({
    state: "visible",
    timeout: 30_000
  });
  const currentTab = page.locator('[aria-current="page"]');
  if ((await currentTab.count()) !== 1) {
    throw new Error("La navegacion principal debe exponer exactamente una vista activa con aria-current=page.");
  }
}

async function runAccessibilitySmoke() {
  const startedProcesses = [];
  let browser;

  try {
    seedValidationUsers();
    await ensureBackend(startedProcesses);
    await ensureFrontend(startedProcesses);

    browser = await launchBrowserOverCdp(startedProcesses);
    const password = readValidationPassword();

    const loginContext = await browser.newContext();
    try {
      const page = await loginContext.newPage();
      await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
      await assertLoginAccessibility(page);
    } finally {
      await loginContext.close();
    }

    const adminContext = await browser.newContext();
    try {
      const page = await adminContext.newPage();
      await login(page, "admin.qa", password);
      await assertMainShellAccessibility(page);
      await page.getByRole("heading", { name: "Dashboard Operacional" }).waitFor({
        state: "visible",
        timeout: 30_000
      });
      await page.getByRole("region", { name: "Mapa operativo de eventos" }).waitFor({
        state: "visible",
        timeout: 30_000
      });
      await page.getByRole("img", { name: "Delitos por hora" }).waitFor({
        state: "visible",
        timeout: 30_000
      });
    } finally {
      await adminContext.close();
    }

    const consultaContext = await browser.newContext();
    try {
      const page = await consultaContext.newPage();
      await login(page, "consulta.qa", password);
      await assertMainShellAccessibility(page);
      await page.locator("#id_comisaria").waitFor({ state: "visible", timeout: 30_000 });
      if ((await page.locator("#region").count()) !== 0) {
        throw new Error("La vista consulta no debe exponer el selector jerarquico de region.");
      }
      if ((await page.locator('[data-testid="tab-carga-datos"]').count()) !== 0) {
        throw new Error("La vista consulta no debe exponer la pestana de carga.");
      }
    } finally {
      await consultaContext.close();
    }

    console.log("Accesibilidad smoke completada correctamente.");
  } finally {
    if (browser) {
      await browser.close();
    }

    for (const process of startedProcesses.reverse()) {
      stopProcessTree(process);
    }
  }
}

runAccessibilitySmoke().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
