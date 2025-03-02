"""
Trade logging module
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
import pandas as pd
from loguru import logger
from ..utils.formatting import DecimalEncoder

class TradeLogger:
    """Logs and stores trade information"""
    
    def __init__(
        self,
        log_dir: str = "logs/trades",
        trade_file: str = "trades.json",
        backup_interval: int = 100
    ):
        """
        Initialize trade logger
        
        Args:
            log_dir: Directory for trade logs
            trade_file: Trade history filename
            backup_interval: Number of trades between backups
        """
        self.log_dir = Path(log_dir)
        self.trade_file = self.log_dir / trade_file
        self.backup_interval = backup_interval
        self.trades: List[Dict] = []
        self.trade_count = 0
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing trades
        self._load_trades()
        
    def log_trade(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        timestamp: datetime,
        trade_type: str = "market",
        fees: Optional[Decimal] = None,
        **kwargs
    ) -> None:
        """
        Log a trade
        
        Args:
            symbol: Trading pair
            side: Trade side (buy/sell)
            amount: Trade amount
            price: Trade price
            timestamp: Trade timestamp
            trade_type: Order type
            fees: Optional trading fees
            **kwargs: Additional trade details
        """
        try:
            trade = {
                "symbol": symbol,
                "side": side,
                "amount": str(amount),
                "price": str(price),
                "timestamp": timestamp.isoformat(),
                "type": trade_type,
                "fees": str(fees) if fees else None,
                **kwargs
            }
            
            self.trades.append(trade)
            self.trade_count += 1
            
            # Save periodically
            if self.trade_count % self.backup_interval == 0:
                self._save_trades()
                
            logger.info(
                f"Logged {side} trade: {amount} {symbol} @ {price}"
            )
            
        except Exception as e:
            logger.error(f"Error logging trade: {str(e)}")
            
    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get filtered trades
        
        Args:
            symbol: Optional symbol filter
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            List of matching trades
        """
        filtered = self.trades
        
        if symbol:
            filtered = [t for t in filtered if t["symbol"] == symbol]
            
        if start_time:
            filtered = [
                t for t in filtered
                if datetime.fromisoformat(t["timestamp"]) >= start_time
            ]
            
        if end_time:
            filtered = [
                t for t in filtered
                if datetime.fromisoformat(t["timestamp"]) <= end_time
            ]
            
        return filtered
        
    def to_dataframe(self) -> pd.DataFrame:
        """Convert trades to DataFrame"""
        return pd.DataFrame(self.trades)
        
    def _load_trades(self) -> None:
        """Load trades from file"""
        try:
            if self.trade_file.exists():
                with open(self.trade_file) as f:
                    self.trades = json.load(f)
                self.trade_count = len(self.trades)
                logger.info(f"Loaded {self.trade_count} trades")
        except Exception as e:
            logger.error(f"Error loading trades: {str(e)}")
            self.trades = []
            
    def _save_trades(self) -> None:
        """Save trades to file"""
        try:
            # Create backup
            if self.trade_file.exists():
                backup_file = self.trade_file.with_suffix(".json.bak")
                self.trade_file.rename(backup_file)
                
            # Save current trades
            with open(self.trade_file, 'w') as f:
                json.dump(
                    self.trades,
                    f,
                    cls=DecimalEncoder,
                    indent=2
                )
                
            logger.info(f"Saved {len(self.trades)} trades")
            
        except Exception as e:
            logger.error(f"Error saving trades: {str(e)}")
            
            # Restore from backup
            if backup_file.exists():
                backup_file.rename(self.trade_file)
