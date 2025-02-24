"""
Unit tests for configuration management
"""

import os
import pytest
import yaml
from pathlib import Path
from app.config import ConfigManager

@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory with test files"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create test config files
    files = {
        "exchange_config.yaml": {
            "default_exchange": "ftx",
            "exchanges": {
                "ftx": {
                    "api_url": "https://ftx.com/api",
                    "websocket_url": "wss://ftx.com/ws/",
                    "test_mode": True
                }
            }
        },
        "risk_config.yaml": {
            "position_sizing": {
                "max_size": 0.1,
                "risk_per_trade": 0.01
            },
            "stop_loss": {
                "default_stop": 0.02
            }
        },
        "gui_config.yaml": {
            "window": {
                "title": "Trading Bot",
                "width": 1600,
                "height": 900
            }
        }
    }
    
    for filename, content in files.items():
        config_file = config_dir / filename
        with open(config_file, "w") as f:
            yaml.dump(content, f)
    
    return config_dir

@pytest.fixture
def config_manager(config_dir):
    """Create a ConfigManager instance"""
    return ConfigManager(config_dir)

def test_config_initialization(config_manager):
    """Test configuration initialization"""
    assert config_manager is not None
    assert config_manager.config_dir.exists()

def test_load_exchange_config(config_manager):
    """Test loading exchange configuration"""
    config = config_manager.get_exchange_config()
    
    assert config["default_exchange"] == "ftx"
    assert "exchanges" in config
    assert "ftx" in config["exchanges"]
    assert config["exchanges"]["ftx"]["test_mode"] is True

def test_load_risk_config(config_manager):
    """Test loading risk configuration"""
    config = config_manager.get_risk_config()
    
    assert "position_sizing" in config
    assert config["position_sizing"]["max_size"] == 0.1
    assert config["position_sizing"]["risk_per_trade"] == 0.01
    assert config["stop_loss"]["default_stop"] == 0.02

def test_load_gui_config(config_manager):
    """Test loading GUI configuration"""
    config = config_manager.get_gui_config()
    
    assert "window" in config
    assert config["window"]["title"] == "Trading Bot"
    assert config["window"]["width"] == 1600
    assert config["window"]["height"] == 900

def test_config_validation(config_dir):
    """Test configuration validation"""
    # Create invalid config
    invalid_config = config_dir / "exchange_config.yaml"
    with open(invalid_config, "w") as f:
        yaml.dump({"invalid": "config"}, f)
    
    with pytest.raises(ValueError):
        ConfigManager(config_dir)

def test_config_override(config_dir):
    """Test configuration override with environment variables"""
    # Set environment variables
    os.environ["TRADING_BOT_FTX_API_URL"] = "https://test.ftx.com/api"
    os.environ["TRADING_BOT_MAX_POSITION_SIZE"] = "0.2"
    
    config_manager = ConfigManager(config_dir)
    
    # Check if environment variables override config
    exchange_config = config_manager.get_exchange_config()
    assert exchange_config["exchanges"]["ftx"]["api_url"] == "https://test.ftx.com/api"
    
    risk_config = config_manager.get_risk_config()
    assert risk_config["position_sizing"]["max_size"] == 0.2
    
    # Clean up
    del os.environ["TRADING_BOT_FTX_API_URL"]
    del os.environ["TRADING_BOT_MAX_POSITION_SIZE"]

def test_config_update(config_manager):
    """Test updating configuration"""
    # Update exchange config
    exchange_config = config_manager.get_exchange_config()
    exchange_config["exchanges"]["ftx"]["test_mode"] = False
    config_manager.update_exchange_config(exchange_config)
    
    # Verify update
    new_config = config_manager.get_exchange_config()
    assert new_config["exchanges"]["ftx"]["test_mode"] is False

def test_config_reload(config_dir):
    """Test configuration reload"""
    config_manager = ConfigManager(config_dir)
    
    # Modify config file
    exchange_config = config_dir / "exchange_config.yaml"
    with open(exchange_config, "r") as f:
        config = yaml.safe_load(f)
    
    config["default_exchange"] = "binance"
    
    with open(exchange_config, "w") as f:
        yaml.dump(config, f)
    
    # Reload config
    config_manager.reload()
    new_config = config_manager.get_exchange_config()
    assert new_config["default_exchange"] == "binance"

def test_missing_config_file(config_dir):
    """Test handling of missing config files"""
    # Remove a config file
    (config_dir / "gui_config.yaml").unlink()
    
    with pytest.raises(FileNotFoundError):
        ConfigManager(config_dir)

def test_invalid_config_format(config_dir):
    """Test handling of invalid config format"""
    # Create config with invalid YAML
    with open(config_dir / "exchange_config.yaml", "w") as f:
        f.write("invalid: yaml: content: :")
    
    with pytest.raises(yaml.YAMLError):
        ConfigManager(config_dir)

def test_config_type_validation(config_manager):
    """Test configuration type validation"""
    exchange_config = config_manager.get_exchange_config()
    
    # Test with invalid type
    exchange_config["exchanges"]["ftx"]["test_mode"] = "not_a_boolean"
    
    with pytest.raises(ValueError):
        config_manager.update_exchange_config(exchange_config)
