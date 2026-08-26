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

function Get-NoethysBootstrapPython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $py) {
        try {
            & py -3.10 -c "import sys; print(sys.executable)" *> $null
            if ($LASTEXITCODE -eq 0) {
                return @{ Command = 'py'; Args = @('-3.10') }
            }
        }
        catch {}
    }

    foreach ($candidate in @('python', 'python3')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            try {
                $version = & $candidate -c "import sys; print('%d.%d' % sys.version_info[:2])"
                if ($LASTEXITCODE -eq 0 -and $version.Trim() -eq '3.10') {
                    return @{ Command = $candidate; Args = @() }
                }
            }
            catch {}
        }
    }

    throw 'Python 3.10 est introuvable. Installer Python 3.10 pour Windows puis relancer DEV-Noethys.cmd.'
}

function Get-NoethysFileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        try {
            $hash = $sha256.ComputeHash($stream)
        }
        finally {
            $sha256.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }

    return ([System.BitConverter]::ToString($hash)).Replace('-', '')
}

if (-not (Test-Path $Python)) {
    Write-Host 'Premiere utilisation : creation du venv Python 3.10...'
    $bootstrap = Get-NoethysBootstrapPython
    $bootstrapArgs = @($bootstrap.Args) + @('-m', 'venv', $Venv)
    & $bootstrap.Command @bootstrapArgs
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de creer le venv Python 3.10.' }
}

$hash1 = Get-NoethysFileSha256 $ReqBuild
$hash2 = Get-NoethysFileSha256 $ReqRuntime
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

Write-Host 'Application des correctifs Python 3/wxPhoenix connus...'
& $Python (Join-Path $Root 'scripts\apply_py3_runtime_source_fixes.py')
if ($LASTEXITCODE -ne 0) { throw 'Echec application des correctifs Python 3/wxPhoenix.' }

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
