# Push ONLY this repo to a second GitHub account.
# Your main GitHub login stays the default for all other projects on this PC.
#
# Usage:
#   .\scripts\push-other-github.ps1 -GitHubUser "submission-username" -RepoName "disaster-response-platform"
#
# HTTPS (default): username is embedded in the remote URL so Windows Credential Manager
# can store a separate PAT for this account without replacing your primary one.
#
# SSH (recommended if you push to both accounts often):
#   1. Run .\scripts\setup-second-github-ssh.ps1 once
#   2. .\scripts\push-other-github.ps1 -GitHubUser "..." -UseSsh -SshHostAlias "github-submit"

param(
    [Parameter(Mandatory = $true)]
    [string]$GitHubUser,

    [Parameter(Mandatory = $false)]
    [string]$RepoName = "disaster-response-platform",

    [Parameter(Mandatory = $false)]
    [switch]$UseSsh,

    [Parameter(Mandatory = $false)]
    [string]$SshHostAlias = "github-submit"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".git")) {
    Write-Error "No .git folder here. Run from disaster-platform after git init."
}

if ($UseSsh) {
    $remoteUrl = "git@${SshHostAlias}:${GitHubUser}/${RepoName}.git"
} else {
    # IMPORTANT: GitHubUser@ in URL keeps credentials separate from your primary account.
    $remoteUrl = "https://${GitHubUser}@github.com/${GitHubUser}/${RepoName}.git"
}

Write-Host "This repo only — remote: $remoteUrl"
Write-Host "Other folders on this PC keep using your normal GitHub account."
Write-Host ""

if (-not $UseSsh) {
    Write-Host "Before push (second account in browser):"
    Write-Host "  1. Create empty repo: $RepoName"
    Write-Host "  2. PAT (classic) with 'repo' scope for user: $GitHubUser"
    Write-Host "  3. When prompted: username = $GitHubUser, password = PAT (not GitHub password)"
    Write-Host ""
    Write-Host "Do NOT delete all github.com credentials — that breaks your primary account."
    Write-Host ""
} else {
    Write-Host "Using SSH alias '$SshHostAlias' — see scripts/setup-second-github-ssh.ps1"
    Write-Host ""
}

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
    Write-Host "Push failed."
    if (-not $UseSsh) {
        Write-Host "If it used the wrong account, set remote again with this script (username in URL)."
        Write-Host "Or switch to SSH: setup-second-github-ssh.ps1 then -UseSsh"
    }
}
