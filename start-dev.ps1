param(
    [bool]$OpenBrowser = $true
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"
$backendPython = Join-Path $backendPath ".venv\Scripts\python.exe"
$backendRequirements = Join-Path $backendPath "requirements.txt"
$backendDevRequirements = Join-Path $backendPath "requirements-dev.txt"

if (-not (Test-Path -LiteralPath $backendPath)) {
    throw "No se encontro la carpeta del backend en: $backendPath"
}

if (-not (Test-Path -LiteralPath $frontendPath)) {
    throw "No se encontro la carpeta del frontend en: $frontendPath"
}

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "No se encontro el entorno virtual del backend en: $backendPython"
}

$backendCommand = @"
Set-Location -LiteralPath '$backendPath'
Write-Host 'Verificando dependencias del backend...'
& '$backendPython' -c "import click, fastapi, uvicorn, psycopg2, dotenv, openpyxl, jwt, multipart"
`$needsInstall = `$LASTEXITCODE -ne 0

if (-not `$needsInstall) {
    & '$backendPython' -m pip check
    `$needsInstall = `$LASTEXITCODE -ne 0
}

if (`$needsInstall) {
    Write-Host 'Dependencias incompletas. Instalando/actualizando desde requirements...'
    if (Test-Path -LiteralPath '$backendDevRequirements') {
        & '$backendPython' -m pip install -r '$backendDevRequirements'
    } else {
        & '$backendPython' -m pip install -r '$backendRequirements'
    }

    if (`$LASTEXITCODE -ne 0) {
        Write-Error 'No se pudieron instalar las dependencias del backend.'
        exit `$LASTEXITCODE
    }
}

& '$backendPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"@

$frontendCommand = @"
Set-Location -LiteralPath '$frontendPath'
npm run dev
"@

Start-Process -FilePath "powershell.exe" `
    -WorkingDirectory $backendPath `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $backendCommand
    )

Start-Process -FilePath "powershell.exe" `
    -WorkingDirectory $frontendPath `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $frontendCommand
    )

if ($OpenBrowser) {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5173"
}
