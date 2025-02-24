# Trading Bot Installation Guide

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux operating system
- At least 4GB RAM
- Stable internet connection
- (Optional) NVIDIA GPU for accelerated chart rendering

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/trading_bot.git
cd trading_bot
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install optional GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Exchange API Keys
FTX_API_KEY=your_api_key
FTX_API_SECRET=your_api_secret
FTX_SUBACCOUNT=your_subaccount_name

# Risk Management
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
MAX_DRAWDOWN=0.1
DAILY_LOSS_LIMIT=0.05

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# GUI
THEME=dark
WINDOW_WIDTH=1280
WINDOW_HEIGHT=800
```

### 5. Configure Exchange Settings

Update `config/exchange_config.yaml` with your preferred settings:

```yaml
default_exchange: ftx
exchanges:
  ftx:
    api_url: https://ftx.com/api
    websocket_url: wss://ftx.com/ws/
    test_mode: false
```

### 6. Configure Risk Management

Update `config/risk_config.yaml` with your risk parameters:

```yaml
position_sizing:
  max_size: 0.1
  risk_per_trade: 0.01
  sizing_method: fixed_risk

stop_loss:
  default_stop: 0.02
  trailing_stop: 0.01
  break_even: 0.01
```

### 7. Verify Installation

Run the test suite to verify everything is working:

```bash
pytest tests/
```

### 8. Start the Trading Bot

```bash
python main.py
```

## Troubleshooting

### Common Issues

1. **Package Installation Errors**
   ```bash
   # If you encounter SSL errors
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

2. **GPU Support Issues**
   ```bash
   # Check CUDA availability
   python -c "import torch; print(torch.cuda.is_available())"
   ```

3. **Exchange Connection Issues**
   - Verify API keys are correct
   - Check internet connection
   - Ensure VPN is disabled (if applicable)

4. **GUI Display Issues**
   ```bash
   # Install additional Qt dependencies
   pip install PyQt5-tools
   ```

### System-Specific Setup

#### Windows
- Install Visual C++ Build Tools
- Add Python to PATH
- Install Windows Terminal (recommended)

#### macOS
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install additional dependencies
brew install cmake
brew install qt5
```

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    build-essential \
    cmake \
    qt5-default
```

## Updating

To update the trading bot:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run database migrations (if applicable)
python scripts/migrate.py
```

## Security Considerations

1. **API Key Security**
   - Use environment variables for API keys
   - Never commit API keys to version control
   - Use read-only API keys when possible

2. **System Security**
   - Keep Python and dependencies updated
   - Use a dedicated user account
   - Enable system firewall
   - Use strong passwords

3. **Network Security**
   - Use HTTPS/WSS connections
   - Consider using a VPN
   - Monitor network traffic

## Support

For additional support:
- Check the [FAQ](faq.md)
- Submit issues on GitHub
- Join our Discord community
- Contact support@tradingbot.com
