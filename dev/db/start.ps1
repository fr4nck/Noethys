$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $Here 'compose.yml'
$EnvFile = Join-Path $Here '.env'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker est introuvable. Installer/démarrer Docker Desktop avant de continuer.'
}
if (-not (Test-Path $EnvFile)) {
    throw "Configuration absente : copier $Here\.env.example vers $Here\.env puis renseigner les mots de passe."
}

& docker compose --env-file $EnvFile -f $ComposeFile up -d
if ($LASTEXITCODE -ne 0) { throw 'Échec du démarrage Docker Compose.' }

Write-Host 'Attente de MySQL 5.5...' -ForegroundColor Cyan
$status = ''
for ($i = 0; $i -lt 30; $i++) {
    $status = (& docker inspect --format '{{.State.Health.Status}}' noethys-mysql55 2>$null)
    if ($status -eq 'healthy') { break }
    Start-Sleep -Seconds 2
}
if ($status -ne 'healthy') { throw "MySQL n'est pas sain (état : $status)." }

$version = & docker compose --env-file $EnvFile -f $ComposeFile exec -T mysql55 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -Nse "SELECT VERSION();"'
if ($LASTEXITCODE -ne 0) { throw 'MySQL répond mais la vérification de version a échoué.' }
$binding = & docker port noethys-mysql55 3306/tcp
Write-Host "MySQL prêt : $version — $binding" -ForegroundColor Green
