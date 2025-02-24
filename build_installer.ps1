# Build script for creating the Trading Bot installer

# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "Starting Trading Bot installer build process..."

# Create necessary directories
Write-Host "Creating build directories..."
New-Item -ItemType Directory -Force -Path "dist"
New-Item -ItemType Directory -Force -Path "installer"

# Install required Python packages
Write-Host "Installing required packages..."
python -m pip install -r requirements.txt
python -m pip install pyinstaller

# Build the executable using PyInstaller
Write-Host "Building executable with PyInstaller..."
pyinstaller trading_bot.spec

# Check if Inno Setup is installed
$innoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    Write-Host "Inno Setup not found. Please install Inno Setup 6 from https://jrsoftware.org/isdl.php"
    exit 1
}

# Build the installer
Write-Host "Building installer with Inno Setup..."
& $innoSetupPath "installer.iss"

Write-Host "Build process completed!"
Write-Host "Installer can be found in the 'installer' directory."
