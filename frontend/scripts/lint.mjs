import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { transform } from "esbuild";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const sourceRoots = [
  path.join(rootDir, "src"),
  path.join(rootDir, "tests"),
  path.join(rootDir, "scripts")
];
const failures = [];

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nestedFiles = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(directory, entry.name);

      if (entry.isDirectory()) {
        return collectFiles(entryPath);
      }

      return entryPath;
    })
  );

  return nestedFiles.flat();
}

function getLoader(filePath) {
  const extension = path.extname(filePath);

  if (extension === ".jsx") {
    return "jsx";
  }

  return "js";
}

async function lintSourceFiles() {
  const files = (
    await Promise.all(sourceRoots.map((directory) => collectFiles(directory)))
  )
    .flat()
    .filter((filePath) => [".js", ".jsx", ".mjs"].includes(path.extname(filePath)));

  await Promise.all(
    files.map(async (filePath) => {
      const source = await readFile(filePath, "utf8");

      try {
        await transform(source, {
          loader: getLoader(filePath),
          format: "esm",
          jsx: "automatic"
        });
      } catch (error) {
        failures.push(`${path.relative(rootDir, filePath)}: ${error.message}`);
      }
    })
  );
}

async function lintProductionEnv() {
  const envPath = path.join(rootDir, ".env.production");
  let rawEnv = "";

  try {
    rawEnv = await readFile(envPath, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") {
      return;
    }

    throw error;
  }

  const apiBaseUrlLine = rawEnv
    .split(/\r?\n/u)
    .find((line) => line.trim().startsWith("VITE_API_BASE_URL="));

  const apiBaseUrl = apiBaseUrlLine ? apiBaseUrlLine.split("=", 2)[1].trim() : "";
  if (/localhost|127\.0\.0\.1/u.test(apiBaseUrl)) {
    failures.push(".env.production: VITE_API_BASE_URL no puede apuntar a localhost ni a 127.0.0.1.");
  }
}

await Promise.all([lintSourceFiles(), lintProductionEnv()]);

if (failures.length) {
  console.error("Frontend lint failed:");
  failures.forEach((failure) => {
    console.error(`- ${failure}`);
  });
  process.exit(1);
}

console.log("Frontend lint OK");
