$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'
$ReqMarker = Join-Path $Venv '.noethys-requirements.sha256'
$ReqBuild = Join-Path $Root 'requirements-build.txt'
$ReqRuntime = Join-Path $Root 'requirements.txt'

Write-Host ''
Write-Host '=== Noethys - recette locale Windows ==='
Write-Host "Depot : $Root"

if (-not (Test-Path $Python)) {
    Write-Host 'Premiere utilisation : creation du venv Python 3.10...'
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($null -eq $py) {
        throw 'Le lanceur Python "py" est introuvable. Installer Python 3.10 pour Windows puis relancer.'
    }
    & py -3.10 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de creer le venv Python 3.10.' }
}

$hash1 = (Get-FileHash $ReqBuild -Algorithm SHA256).Hash
$hash2 = (Get-FileHash $ReqRuntime -Algorithm SHA256).Hash
$requirementsHash = "$hash1-$hash2"
$currentHash = ''
if (Test-Path $ReqMarker) {
    $currentHash = (Get-Content $ReqMarker -Raw).Trim()
}

if ($currentHash -ne $requirementsHash) {
    Write-Host 'Installation/mise a jour des dependances (uniquement quand requirements change)...'
    & $Python -m pip install --upgrade pip wheel
    if ($LASTEXITCODE -ne 0) { throw 'Echec mise a jour pip/wheel.' }
    & $Python -m pip install -r $ReqBuild
    if ($LASTEXITCODE -ne 0) { throw 'Echec installation des dependances Noethys.' }
    Set-Content -Path $ReqMarker -Value $requirementsHash -Encoding ASCII
}
else {
    Write-Host 'Dependances deja installees : aucun telechargement.'
}

$Portable = Join-Path $Root 'noethys\Portable'
New-Item -ItemType Directory -Path $Portable -Force | Out-Null

Write-Host ''
Write-Host 'Lancement depuis les sources avec diagnostics complets...'
Write-Host 'Logs : noethys\Portable\journal.log / noethys_actions.log / noethys_crash.log / noethys_hang.log'
Write-Host ''

& $Python (Join-Path $Root 'scripts\run_noethys_dev.py')
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ''
    Write-Host "Noethys a quitte avec le code $code. Voir les logs dans noethys\Portable." -ForegroundColor Yellow
}
exit $code
