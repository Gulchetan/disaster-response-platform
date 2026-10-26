# Clear cached GitHub HTTPS login for ONE username, then push (you enter a fresh PAT).
# Use when you see: Permission to User/repo.git denied to User (403)
#
# Usage:
#   .\scripts\refresh-github-credentials.ps1 -GitHubUser "Gulchetan" -RepoName "disaster-response-platform"

param(
    [Parameter(Mandatory = $true)]
    [string]$GitHubUser,

    [Parameter(Mandatory = $false)]
    [string]$RepoName = "disaster-response-platform"
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..

Write-Host "=== Fix GitHub 403 (wrong or expired token) ==="
Write-Host ""
Write-Host "Create a NEW token on account '$GitHubUser':"
Write-Host "  GitHub -> Settings -> Developer settings -> Personal access tokens"
Write-Host "  -> Tokens (classic) -> Generate new token (classic)"
Write-Host "  Check scope: repo (full control of private repositories)"
Write-Host "  Do NOT use your GitHub account password when Git asks for password."
Write-Host ""

$input = @(
    "protocol=https",
    "host=github.com",
    "username=$GitHubUser"
) -join "`n"

Write-Host "Removing cached HTTPS credentials for username $GitHubUser on github.com ..."
$input | git credential-manager erase 2>$null
if ($LASTEXITCODE -ne 0) {
    $input | git credential reject 2>$null
}

Write-Host ""
Write-Host "When push runs, enter:"
Write-Host "  Username: $GitHubUser"
Write-Host "  Password: paste the NEW classic PAT"
Write-Host ""

$remoteUrl = "https://${GitHubUser}@github.com/${GitHubUser}/${RepoName}.git"
$remoteNames = @(git remote 2>$null | ForEach-Object { $_.Trim() })
if ($remoteNames -contains "origin") {
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
}

Write-Host "Remote: $remoteUrl"
Write-Host "Pushing main..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success: https://github.com/$GitHubUser/$RepoName"
    exit 0
}

Write-Host ""
Write-Host "Still failing? Check:"
Write-Host "  1. Repo exists and is empty: https://github.com/$GitHubUser/$RepoName"
Write-Host "  2. Token is Classic (not fine-grained without Contents: Read and write)"
Write-Host "  3. You are logged into '$GitHubUser' in browser when creating the token"
Write-Host "  4. Try SSH: .\scripts\setup-second-github-ssh.ps1 then push with -UseSsh"
exit 1
