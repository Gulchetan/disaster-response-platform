# Push ONLY this repo to a second GitHub account.
# Your main GitHub login stays the default for all other projects on this PC.
#
# Usage:
#   .\scripts\push-other-github.ps1 -GitHubUser "submission-username" -RepoName "disaster-response-platform"
#
# SSH: run setup-second-github-ssh.ps1 once, then add -UseSsh

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
    $remoteUrl = "https://${GitHubUser}@github.com/${GitHubUser}/${RepoName}.git"
}

Write-Host "This repo only - remote: $remoteUrl"
Write-Host "Other folders on this PC keep using your normal GitHub account."
Write-Host ""

if (-not $UseSsh) {
    Write-Host "Before push (second account in browser):"
    Write-Host "  1. Create empty repo: $RepoName"
    Write-Host "  2. PAT (classic) with repo scope for user: $GitHubUser"
    Write-Host "  3. When prompted: username = $GitHubUser, password = PAT (not GitHub password)"
    Write-Host ""
    Write-Host "Do NOT delete all github.com credentials; that breaks your primary account."
    Write-Host ""
} else {
    Write-Host "Using SSH alias $SshHostAlias - see scripts/setup-second-github-ssh.ps1"
    Write-Host ""
}

$null = git remote get-url origin 2>$null
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
        Write-Host "If it used the wrong account, run this script again (username is in the remote URL)."
        Write-Host "Or use SSH: setup-second-github-ssh.ps1 then push with -UseSsh"
    }
}
