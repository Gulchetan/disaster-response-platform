# One-time setup: second GitHub account via SSH (keeps primary github.com SSH unchanged).
#
# 1. Run this script — it creates a new key (default: id_ed25519_github_submit)
# 2. Add the printed public key to the SECOND GitHub account:
#    Settings -> SSH and GPG keys -> New SSH key
# 3. Append the printed block to: C:\Users\<you>\.ssh\config
# 4. Push this project with:
#    .\scripts\push-other-github.ps1 -GitHubUser "second-user" -UseSsh

param(
    [string]$KeyName = "id_ed25519_github_submit",
    [string]$HostAlias = "github-submit"
)

$ErrorActionPreference = "Stop"
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$keyPath = Join-Path $sshDir $KeyName

if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

if (-not (Test-Path $keyPath)) {
    Write-Host "Creating SSH key at $keyPath ..."
    ssh-keygen -t ed25519 -C "github-second-account" -f $keyPath -N '""'
} else {
    Write-Host "Key already exists: $keyPath"
}

Write-Host ""
Write-Host "========== Add this PUBLIC key to your SECOND GitHub account =========="
Get-Content "$keyPath.pub"
Write-Host "======================================================================="
Write-Host ""
Write-Host "========== Add this block to $sshDir\config (create file if missing) =========="
@"
Host $HostAlias
    HostName github.com
    User git
    IdentityFile $keyPath
    IdentitiesOnly yes
"@
Write-Host "======================================================================="
Write-Host ""
Write-Host "Test (after saving config and adding key on GitHub):"
Write-Host "  ssh -T git@$HostAlias"
Write-Host ""
Write-Host "Then push this repo:"
Write-Host "  cd d:\projects\founding\disaster-platform"
Write-Host "  .\scripts\push-other-github.ps1 -GitHubUser YOUR_SECOND_USER -UseSsh -SshHostAlias $HostAlias"
