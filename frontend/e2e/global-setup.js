import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendDir, "..");
const seedScript = path.resolve(repoRoot, "scripts", "seed_validation_users.py");
const pythonExecutable = path.resolve(repoRoot, "backend", ".venv", "Scripts", "python.exe");

export default async function globalSetup() {
  if (!fs.existsSync(pythonExecutable)) {
    throw new Error(`No se encontro el Python del backend para sembrar usuarios QA: ${pythonExecutable}`);
  }

  execFileSync(pythonExecutable, [seedScript], {
    cwd: repoRoot,
    stdio: "inherit"
  });
}
