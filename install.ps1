param(
    [string]$PythonExe,
    [string]$InstallDirectory = (Join-Path $env:LOCALAPPDATA 'EdgeTabLock')
)

$ErrorActionPreference = 'Stop'
if (-not $PythonExe) {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $PythonExe = & py.exe -3 -c 'import sys; print(sys.executable)'
    } elseif (Get-Command python.exe -ErrorAction SilentlyContinue) {
        $PythonExe = & python.exe -c 'import sys; print(sys.executable)'
    }
}
if (-not $PythonExe -or -not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw 'Install 64-bit Python 3 or specify -PythonExe with its full path.'
}
$PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
$InstallDirectory = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstallDirectory)
if ($InstallDirectory -match '[^\x20-\x7E]' -or $PythonExe -match '[^\x20-\x7E]|%') {
    throw 'Use ASCII paths for -InstallDirectory and -PythonExe. The Python path cannot contain %.'
}
& $PythonExe -c 'import sys; sys.exit(sys.version_info.major != 3 or sys.maxsize <= 2**32)'
if ($LASTEXITCODE -ne 0) { throw '64-bit Python 3 is required.' }

New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'native/host.py') -Destination (Join-Path $InstallDirectory 'host.py') -Force
$launcher = Join-Path $InstallDirectory 'host.cmd'
Set-Content -LiteralPath $launcher -Encoding ascii -Value ('@"{0}" "%~dp0host.py"' -f $PythonExe)
$manifest = Join-Path $InstallDirectory 'host-manifest.json'
$extension = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'extension/manifest.json') -Raw | ConvertFrom-Json
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $digest = $sha.ComputeHash([Convert]::FromBase64String($extension.key))
} finally {
    $sha.Dispose()
}
$extensionId = -join (([BitConverter]::ToString($digest, 0, 16) -replace '-', '').ToLowerInvariant().ToCharArray() |
    ForEach-Object { 'abcdefghijklmnop'[[Convert]::ToInt32([string]$_, 16)] })
@{
    name = 'local.tab_guard'
    description = 'Edge Tab Lock native helper'
    path = $launcher
    type = 'stdio'
    allowed_origins = @("chrome-extension://$extensionId/")
} | ConvertTo-Json | Set-Content -LiteralPath $manifest -Encoding ascii
$registryKey = 'HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\local.tab_guard'
New-Item -Path $registryKey -Force | Out-Null
Set-Item -Path $registryKey -Value $manifest
Write-Host "Helper registered. Load this folder in edge://extensions/:"
Write-Host (Join-Path $PSScriptRoot 'extension')
