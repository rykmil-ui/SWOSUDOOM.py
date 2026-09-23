$ErrorActionPreference = "Stop"

Write-Host "Starting DOOM assignment..."
Write-Host "The decision question will appear in this PowerShell window."
Write-Host ""

$pythonCommand = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
}
else {
    Write-Host "Python was not found."
    Read-Host "Press Enter to close"
    exit 1
}

& $pythonCommand -c "import pygame" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pygame-ce..."
    & $pythonCommand -m pip install pygame-ce
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not install pygame-ce."
        Read-Host "Press Enter to close"
        exit 1
    }
}

& $pythonCommand "$PSScriptRoot\python_doom_enhanced_assignment_v9.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The game exited with an error."
    Read-Host "Press Enter to close"
}
