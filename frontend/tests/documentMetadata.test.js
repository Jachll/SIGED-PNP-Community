import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "..");
const indexHtmlPath = path.resolve(frontendDir, "index.html");

test("index.html expone lang es y el titulo de ETAPA 2", () => {
  const html = fs.readFileSync(indexHtmlPath, "utf8");

  assert.match(html, /<html lang="es">/u);
  assert.match(html, /<title>SIGED-PNP - ETAPA 2<\/title>/u);
});
