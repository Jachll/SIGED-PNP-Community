import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const sampleCsvPath = path.resolve(repoRoot, "database", "sample_data", "eventos_delictivos_sample.csv");

function readValidationPassword() {
  const envPath = path.resolve(repoRoot, "backend", ".env");
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

async function login(page, username) {
  await page.goto("/");
  await page.getByTestId("login-username").fill(username);
  await page.getByTestId("login-password").fill(readValidationPassword());
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("tab-dashboard-operacional")).toBeVisible();
}

async function readNumericTestId(page, testId) {
  const locator = page.getByTestId(testId);
  await expect(locator).toContainText(/\d+/u);
  return Number.parseInt(await locator.innerText(), 10);
}

test("rol admin expone todas las vistas y filtros jerarquicos", async ({ page }) => {
  await login(page, "admin.qa");

  await expect(page.locator(".session-card")).toContainText("Administrador");
  await expect(page.getByTestId("tab-dashboard-operacional")).toBeVisible();
  await expect(page.getByTestId("tab-analisis-temporal")).toBeVisible();
  await expect(page.getByTestId("tab-analitica-operativa")).toBeVisible();
  await expect(page.getByTestId("tab-carga-datos")).toBeVisible();
  await expect(page.locator("#region")).toBeVisible();
  await expect(page.locator("#id_comisaria")).toHaveCount(0);

  expect(await readNumericTestId(page, "dashboard-event-count")).toBeGreaterThan(0);
});

test("flujo smoke E2E analista: login -> dashboard -> carga -> analitica", async ({ page }) => {
  await login(page, "analista.qa");

  await expect(page.locator(".session-card")).toContainText("Analista");

  expect(await readNumericTestId(page, "dashboard-event-count")).toBeGreaterThan(0);

  await page.getByTestId("tab-carga-datos").click();
  await expect(page.getByTestId("upload-input")).toBeVisible();
  await page.getByTestId("upload-input").setInputFiles(sampleCsvPath);
  await page.getByTestId("upload-submit").click();

  await expect(page.getByTestId("selected-batch-status")).toContainText(/Completado/u, {
    timeout: 30_000
  });
  const promotedText = await page.getByTestId("selected-batch-promovidos").textContent();
  expect(Number.parseInt(promotedText ?? "0", 10)).toBeGreaterThan(0);

  await page.getByTestId("tab-analitica-operativa").click();
  await expect(page.getByTestId("hotspots-list")).toBeVisible();
  await expect(page.getByTestId("zonas-list")).toBeVisible();
  await expect(page.getByTestId("recommendations-list")).toBeVisible();

  const hotspots = Number.parseInt(await page.getByTestId("analytics-hotspots-count").innerText(), 10);
  const zonas = Number.parseInt(await page.getByTestId("analytics-zonas-count").innerText(), 10);
  const recomendaciones = Number.parseInt(
    await page.getByTestId("analytics-recomendaciones-count").innerText(),
    10
  );

  expect(hotspots).toBeGreaterThan(0);
  expect(zonas).toBeGreaterThan(0);
  expect(recomendaciones).toBeGreaterThan(0);
});

test("rol consulta solo expone vistas de lectura con fallback simple por comisaria", async ({ page }) => {
  await login(page, "consulta.qa");

  await expect(page.locator(".session-card")).toContainText("Consulta");
  await expect(page.getByTestId("tab-dashboard-operacional")).toBeVisible();
  await expect(page.getByTestId("tab-analisis-temporal")).toBeVisible();
  await expect(page.getByTestId("tab-carga-datos")).toHaveCount(0);
  await expect(page.getByTestId("tab-analitica-operativa")).toHaveCount(0);
  await expect(page.locator("#id_comisaria")).toBeVisible();
  await expect(page.locator("#region")).toHaveCount(0);

  expect(await readNumericTestId(page, "dashboard-event-count")).toBeGreaterThan(0);

  await page.getByTestId("tab-analisis-temporal").click();
  await expect(page.getByRole("heading", { name: "Analisis Temporal" })).toBeVisible();
});
