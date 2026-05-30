# Run from PowerShell: .\scripts\init-and-push.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

git add .
git status

$msg = "Initial CosmoCore: Swiss Ephemeris engine, FastAPI, Celery, Expo mobile"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing new to commit or commit failed."
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh auth status
    gh repo create cosmocore --private --source=. --remote=origin --push
} else {
    Write-Host "Install GitHub CLI: https://cli.github.com/"
    Write-Host "Or add remote manually — see GITHUB_SETUP.md"
}
