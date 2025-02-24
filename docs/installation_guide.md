# Trading Bot Installation Guide

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux operating system
- At least 4GB RAM
- Stable internet connection
- (Optional) NVIDIA GPU for accelerated chart rendering

## Prerequisites

1. Install Python 3.9 or later from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Also check "Install for all users"

2. Install Inno Setup 6 from [jrsoftware.org](https://jrsoftware.org/isdl.php)
   - Download the "innosetup-6.x.x.exe" installer
   - Run the installer and follow the default installation options

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/trading_bot.git
cd trading_bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Build the Installer

1. Open PowerShell as Administrator and navigate to the trading bot directory:
   ```powershell
   cd C:\Users\John\CascadeProjects\trading_bot
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Run the installer script:
   ```powershell
   python installer.iss
   ```

## Installing the Trading Bot

1. Run the installer generated in the previous step
2. Follow the installation wizard
3. Choose whether to create a desktop shortcut (selected by default)
4. Complete the installation

## Post-Installation

1. The Trading Bot will be installed in the default location: `C:\Program Files\Trading Bot`
2. A desktop shortcut will be created if selected during installation
3. The application can be launched from:
   - Desktop shortcut
   - Start menu
   - Quick launch bar (if selected during installation)

## Usage

After installation, you can run the trading bot using the following command:
```bash
python run_bot.py
```

## Uninstalling

To uninstall the Trading Bot:

1. Go to Windows Settings > Apps > Apps & features
2. Search for "Trading Bot"
3. Click "Uninstall"
4. Follow the uninstallation wizard

## Troubleshooting

If you encounter any issues:

1. **Python not found error**:
   - Make sure Python is installed and added to PATH
   - Try running `python --version` in PowerShell to verify

2. **pip not found error**:
   - Try using `python -m pip` instead of just `pip`
   - Verify pip is installed: `python -m ensurepip`

3. **PyInstaller errors**:
   - Make sure all dependencies are installed: `python -m pip install -r requirements.txt`
   - Try reinstalling PyInstaller: `python -m pip install --upgrade pyinstaller`

4. **Inno Setup not found**:
   - Verify Inno Setup is installed in the default location
   - Add Inno Setup to PATH if installed in a different location

For additional help, please check the [GitHub issues](https://github.com/yourusername/trading_bot/issues) or create a new issue.
