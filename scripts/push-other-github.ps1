# Push this repo to a GitHub account that is NOT the one saved in Windows Credential Manager.
# Usage (from disaster-platform folder):
#   .\scripts\push-other-github.ps1 -GitHubUser "your-other-username" -RepoName "disaster-response-platform"
#
# Before running:
# 1. Log into the OTHER GitHub account in the browser.
# 2. Create an empty repo (no README) named $RepoName.
# 3. Create a Personal Access Token (Classic): repo scope.
#    Settings -> Developer settings -> Personal access tokens -> Generate new token (classic)

param(
    [Parameter(Mandatory = $true)]
    [string]$GitHubUser,

    [Parameter(Mandatory = $false)]
    [string]$RepoName = "disaster-response-platform"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".git")) {
    Write-Error "No .git folder here. Run from disaster-platform after git init."
}

$remoteUrl = "https://github.com/$GitHubUser/$RepoName.git"

Write-Host "Remote will be: $remoteUrl"
Write-Host ""
Write-Host "Step A — Remove wrong GitHub login from Windows (if push used old account):"
Write-Host "  Win+R -> control /name Microsoft.CredentialManager"
Write-Host "  Windows Credentials -> remove entries for git:https://github.com"
Write-Host ""
Write-Host "Step B — When git asks for password, use a PAT (not your GitHub password)."
Write-Host ""

$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
}

Write-Host "Pushing main to origin..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done: https://github.com/$GitHubUser/$RepoName"
} else {
    Write-Host "Push failed. Try signing in with the other account PAT, or run:"
    Write-Host "  git credential-manager erase https://github.com"
    Write-Host "Then run this script again."
}
