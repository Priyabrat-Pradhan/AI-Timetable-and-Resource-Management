$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend\academic_tms'
$pythonExe = Join-Path $backendRoot '.venv\Scripts\python.exe'
$viteScript = Join-Path $projectRoot 'node_modules\vite\bin\vite.js'

if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Project Python environment is missing.' }
Push-Location $backendRoot
try {
    & $pythonExe manage.py check --database default --fail-level ERROR *> $null
    if ($LASTEXITCODE -ne 0) { throw 'database check failed' }
} catch {
    throw 'The existing MySQL database is not reachable. Start the MySQL service, keep its current database and credentials, then run this launcher again.'
} finally {
    Pop-Location
}
Push-Location $backendRoot
& $pythonExe manage.py migrate --check --noinput *> $null
$migrationExitCode = $LASTEXITCODE
Pop-Location
if ($migrationExitCode -ne 0) { throw 'Database migrations are pending. Run backend\academic_tms\.venv\Scripts\python.exe manage.py migrate before starting the preview.' }

function Get-LocalStatus([string]$Url) {
    try { return (Invoke-WebRequest -Uri $Url -Method Get -SkipHttpErrorCheck -TimeoutSec 2).StatusCode }
    catch { return $null }
}

$apiPort = $null
foreach ($candidatePort in @(8004, 8000, 8001, 8002, 8003)) {
    $loginStatus = Get-LocalStatus "http://127.0.0.1:$candidatePort/api/auth/login/"
    $directoryStatus = Get-LocalStatus "http://127.0.0.1:$candidatePort/api/admin/students/"
    if ($loginStatus -and $directoryStatus -in @(401, 403)) {
        $apiPort = $candidatePort
        break
    }
    if ($loginStatus) { continue } # An old API may be occupying this port; preserve it and use the next one.

    Push-Location $backendRoot
    try {
        Start-Process -FilePath $pythonExe -ArgumentList @('manage.py','runserver',"127.0.0.1:$candidatePort",'--noreload') -WorkingDirectory $backendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backendRoot "runserver-$candidatePort.log") -RedirectStandardError (Join-Path $backendRoot "runserver-$candidatePort-error.log") | Out-Null
    } finally { Pop-Location }

    for ($attempt=0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        $loginStatus = Get-LocalStatus "http://127.0.0.1:$candidatePort/api/auth/login/"
        $directoryStatus = Get-LocalStatus "http://127.0.0.1:$candidatePort/api/admin/students/"
        if ($loginStatus -and $directoryStatus -in @(401, 403)) { $apiPort = $candidatePort; break }
    }
    if ($apiPort) { break }
}
if (-not $apiPort) { throw 'The current Django API could not start. Check the backend runserver-*-error.log files and verify MySQL is running.' }

$apiConfig = "window.SMARTTIME_API_BASE = 'http://127.0.0.1:$apiPort/api';`n"
Set-Content -LiteralPath (Join-Path $projectRoot 'smarttime-config.js') -Value $apiConfig -NoNewline

$previewPort = $null
foreach ($candidate in @(5500, 5501)) {
    if (Get-LocalStatus "http://127.0.0.1:$candidate/login.html") {
        $previewPort = $candidate
        break
    }
}
if (-not $previewPort) {
    if (-not (Test-Path -LiteralPath $viteScript)) { throw 'Vite is missing from node_modules. Run npm install in the project folder.' }
    foreach ($candidate in @(5500, 5501)) {
        $stdoutLog = Join-Path $projectRoot "preview-$candidate.log"
        $stderrLog = Join-Path $projectRoot "preview-$candidate-error.log"
        $viteProcess = Start-Process -FilePath 'node.exe' -ArgumentList @("`"$viteScript`"",'--host','127.0.0.1','--port',[string]$candidate,'--strictPort') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
        for ($attempt=0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Milliseconds 500
            if (Get-LocalStatus "http://127.0.0.1:$candidate/login.html") {
                $previewPort = $candidate
                break
            }
            if ($viteProcess.HasExited) { break }
        }
        if ($previewPort) { break }
        if (-not $viteProcess.HasExited) { Stop-Process -Id $viteProcess.Id -Force -ErrorAction SilentlyContinue }
    }
    if (-not $previewPort) { throw 'Preview server did not start on ports 5500 or 5501. Close other local preview servers and check the preview-*-error.log files.' }
}

Write-Host "Django API ready at http://127.0.0.1:$apiPort/"
Write-Host "Project preview ready at http://127.0.0.1:$previewPort/legacy-index.html"
Start-Process "http://127.0.0.1:$previewPort/legacy-index.html"
