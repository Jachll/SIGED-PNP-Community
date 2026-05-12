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
const sampleCsvPath = path.resolve(repoRoot, "database", "sample_data", "eventos_delictivos_sample.csv");
const pythonExecutable = path.resolve(backendDir, ".venv", "Scripts", "python.exe");
const uvicornExecutable = path.resolve(backendDir, ".venv", "Scripts", "uvicorn.exe");
const seedScript = path.resolve(repoRoot, "scripts", "seed_validation_users.py");
const cleanupLotesScript = path.resolve(repoRoot, "scripts", "cleanup_validation_lotes.py");
const chromeCandidates = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"
];
const backendUrl = "http://127.0.0.1:8000";
const frontendUrl = "http://127.0.0.1:5173";
const QA_LOTE_MARKER = "SIGED_E2E_SMOKE_QA";

function getChromeExecutable() {
  const executable = chromeCandidates.find((candidate) => fs.existsSync(candidate));
  if (!executable) {
    throw new Error("No se encontro Chrome/Edge instalado para el smoke E2E.");
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

function cleanupValidationLotes() {
  if (!fs.existsSync(pythonExecutable)) {
    throw new Error(`No se encontro el Python del backend para limpiar lotes QA: ${pythonExecutable}`);
  }

  execFileSync(pythonExecutable, [cleanupLotesScript, QA_LOTE_MARKER], {
    cwd: repoRoot,
    stdio: "inherit"
  });
}

async function launchBrowserOverCdp(startedProcesses) {
  const chromeExecutable = getChromeExecutable();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "siged-smoke-"));
  const debugPort = 9223 + Math.floor(Math.random() * 500);
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

async function waitForNumericText(page, testId, timeoutMs = 30_000) {
  await page.waitForFunction(
    (currentTestId) => {
      const element = document.querySelector(`[data-testid="${currentTestId}"]`);
      return Boolean(element && /\d+/u.test(element.textContent || ""));
    },
    testId,
    { timeout: timeoutMs }
  );

  const rawText = await page.locator(`[data-testid="${testId}"]`).innerText();
  return Number.parseInt(rawText, 10);
}

async function login(page, username, password) {
  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (error) => {
    pageErrors.push(error instanceof Error ? error.message : String(error));
  });
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
  await page.locator('[data-testid="login-username"]').waitFor({
    state: "visible",
    timeout: 60_000
  });
  await page.locator('[data-testid="login-username"]').fill(username);
  await page.locator('[data-testid="login-password"]').fill(password);
  await page.locator('[data-testid="login-submit"]').click();

  try {
    await page.locator('[data-testid="tab-dashboard-operacional"]').waitFor({ timeout: 60_000 });
  } catch (error) {
    const bannerTexts = [];
    const bannerCount = await page.locator(".status-banner").count();
    const bodyText = ((await page.locator("body").textContent()) ?? "")
      .replace(/\s+/gu, " ")
      .trim()
      .slice(0, 400);

    for (let index = 0; index < bannerCount; index += 1) {
      const bannerText = (await page.locator(".status-banner").nth(index).textContent())?.trim();
      if (bannerText) {
        bannerTexts.push(bannerText);
      }
    }

    const diagnostic = bannerTexts.length
      ? ` Mensajes visibles: ${bannerTexts.join(" | ")}`
      : "";
    const pageErrorDiagnostic = pageErrors.length ? ` Page errors: ${pageErrors.join(" | ")}` : "";
    const consoleErrorDiagnostic = consoleErrors.length ? ` Console errors: ${consoleErrors.join(" | ")}` : "";
    throw new Error(
      `No se completo el login para ${username} en el tiempo esperado.${diagnostic}${pageErrorDiagnostic}${consoleErrorDiagnostic} URL: ${page.url()} BODY: ${bodyText} ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

async function assertSessionRole(page, roleLabel) {
  const sessionText = await page.locator(".session-card").innerText();
  if (!sessionText.includes(roleLabel)) {
    throw new Error(`La sesion activa no corresponde al rol ${roleLabel}. Texto recibido: ${sessionText}`);
  }
}

async function assertTabVisibility(page, { visible = [], hidden = [] }) {
  for (const testId of visible) {
    await page.locator(`[data-testid="${testId}"]`).waitFor({
      state: "visible",
      timeout: 15_000
    });
  }

  for (const testId of hidden) {
    const hiddenCount = await page.locator(`[data-testid="${testId}"]`).count();
    if (hiddenCount !== 0) {
      throw new Error(`La pestana ${testId} no deberia estar visible para este rol.`);
    }
  }
}

async function runSmoke() {
  const startedProcesses = [];
  let browser;

  try {
    seedValidationUsers();
    cleanupValidationLotes();
    await ensureBackend(startedProcesses);
    await ensureFrontend(startedProcesses);

    browser = await launchBrowserOverCdp(startedProcesses);
    const password = readValidationPassword();

    console.log("Paso 1/6: admin con acceso completo y filtros jerarquicos");
    let adminDashboardEvents = 0;
    {
      const adminContext = await browser.newContext();
      const page = await adminContext.newPage();

      try {
        await login(page, "admin.qa", password);
        await assertSessionRole(page, "Administrador");
        await assertTabVisibility(page, {
          visible: [
            "tab-dashboard-operacional",
            "tab-analisis-temporal",
            "tab-analitica-operativa",
            "tab-carga-datos"
          ]
        });
        await page.locator("#region").waitFor({ state: "visible", timeout: 15_000 });
        if ((await page.locator("#id_comisaria").count()) !== 0) {
          throw new Error("El rol admin no deberia usar el fallback simple por comisaria.");
        }
        adminDashboardEvents = await waitForNumericText(page, "dashboard-event-count");
        if (!(adminDashboardEvents > 0)) {
          throw new Error(`El dashboard admin no cargo eventos reales. Valor recibido: ${adminDashboardEvents}`);
        }
      } finally {
        await adminContext.close();
      }
    }

    console.log("Paso 2/6: login analista");
    let dashboardEvents = 0;
    let promoted = 0;
    let hotspots = 0;
    let zonas = 0;
    let recomendaciones = 0;
    {
      const analistaContext = await browser.newContext();
      const page = await analistaContext.newPage();

      try {
        await login(page, "analista.qa", password);
        await assertSessionRole(page, "Analista");

        console.log("Paso 3/6: dashboard con datos reales");
        dashboardEvents = await waitForNumericText(page, "dashboard-event-count");
        if (!(dashboardEvents > 0)) {
          throw new Error(`El dashboard no cargo eventos reales. Valor recibido: ${dashboardEvents}`);
        }

        console.log("Paso 4/6: carga de archivo real");
        await page.locator('[data-testid="tab-carga-datos"]').click();
        await page.locator('[data-testid="upload-input"]').setInputFiles(sampleCsvPath);
        await page.locator('[data-testid="upload-observaciones"]').fill(QA_LOTE_MARKER);
        await page.locator('[data-testid="upload-submit"]').click();
        await page.waitForFunction(
          () => {
            const element = document.querySelector('[data-testid="selected-batch-status"]');
            return Boolean(element && /completado/ui.test(element.textContent || ""));
          },
          undefined,
          { timeout: 45_000 }
        );

        promoted = await waitForNumericText(page, "selected-batch-promovidos");
        if (!(promoted > 0)) {
          throw new Error(`La carga no promovio registros. Valor recibido: ${promoted}`);
        }

        console.log("Paso 5/6: analitica operativa con datos reales");
        await page.locator('[data-testid="tab-analitica-operativa"]').click();
        await page.locator('[data-testid="hotspots-list"]').waitFor({ timeout: 30_000 });
        await page.locator('[data-testid="zonas-list"]').waitFor({ timeout: 30_000 });
        await page.locator('[data-testid="recommendations-list"]').waitFor({ timeout: 30_000 });

        hotspots = await waitForNumericText(page, "analytics-hotspots-count");
        zonas = await waitForNumericText(page, "analytics-zonas-count");
        recomendaciones = await waitForNumericText(page, "analytics-recomendaciones-count");

        if (!(hotspots > 0 && zonas > 0 && recomendaciones > 0)) {
          throw new Error(
            `La analitica no devolvio datos suficientes. hotspots=${hotspots}, zonas=${zonas}, recomendaciones=${recomendaciones}`
          );
        }
      } finally {
        await analistaContext.close();
      }
    }

    console.log("Paso 6/6: consulta en modo solo lectura con fallback simple");
    let consultaDashboardEvents = 0;
    {
      const consultaContext = await browser.newContext();
      const page = await consultaContext.newPage();

      try {
        await login(page, "consulta.qa", password);
        await assertSessionRole(page, "Consulta");
        await assertTabVisibility(page, {
          visible: ["tab-dashboard-operacional", "tab-analisis-temporal"],
          hidden: ["tab-carga-datos", "tab-analitica-operativa"]
        });
        await page.locator("#id_comisaria").waitFor({ state: "visible", timeout: 15_000 });
        if ((await page.locator("#region").count()) !== 0) {
          throw new Error("El rol consulta no deberia exponer el selector jerarquico de region.");
        }
        consultaDashboardEvents = await waitForNumericText(page, "dashboard-event-count");
        if (!(consultaDashboardEvents > 0)) {
          throw new Error(`El dashboard consulta no cargo eventos reales. Valor recibido: ${consultaDashboardEvents}`);
        }
      } finally {
        await consultaContext.close();
      }
    }

    console.log(
      JSON.stringify(
        {
          admin: { eventos: adminDashboardEvents },
          dashboard: { eventos: dashboardEvents },
          carga: { promovidos: promoted },
          analitica: { hotspots, zonas, recomendaciones },
          consulta: { eventos: consultaDashboardEvents }
        },
        null,
        2
      )
    );

    console.log("Smoke E2E completado correctamente.");
  } finally {
    try {
      cleanupValidationLotes();
    } catch (cleanupError) {
      console.error(
        cleanupError instanceof Error
          ? `No se pudo limpiar los lotes QA del smoke: ${cleanupError.message}`
          : `No se pudo limpiar los lotes QA del smoke: ${String(cleanupError)}`
      );
    }

    if (browser) {
      await browser.close();
    }

    for (const process of startedProcesses.reverse()) {
      stopProcessTree(process);
    }
  }
}

runSmoke().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
