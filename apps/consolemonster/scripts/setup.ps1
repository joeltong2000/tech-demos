# Installs the ConsoleMonster module from PowerShell Gallery (free, MIT, no dependencies).
# Works on Windows PowerShell 5.1 and PowerShell 7.
if (Get-Module ConsoleMonster -ListAvailable) {
    $installed = (Get-Module ConsoleMonster -ListAvailable | Select-Object -First 1).Version
    Write-Host "ConsoleMonster $installed is already installed."
    return
}
Install-Module ConsoleMonster -Scope CurrentUser -Force
$version = (Get-Module ConsoleMonster -ListAvailable | Select-Object -First 1).Version
Write-Host "Installed ConsoleMonster $version."
