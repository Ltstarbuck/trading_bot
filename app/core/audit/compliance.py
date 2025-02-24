"""
Trading compliance monitoring
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

class ComplianceMonitor:
    """Monitors trading compliance with rules and limits"""
    
    def __init__(
        self,
        config: Dict,
        check_interval: int = 3600  # 1 hour
    ):
        """
        Initialize compliance monitor
        
        Args:
            config: Configuration dictionary
            check_interval: Seconds between checks
        """
        self.config = config
        self.check_interval = check_interval
        self.last_check = datetime.now()
        self.violations: List[Dict] = []
        
    def check_compliance(
        self,
        positions: Dict,
        trades_df: pd.DataFrame,
        balance: Decimal
    ) -> List[Dict]:
        """
        Check trading compliance
        
        Args:
            positions: Current positions
            trades_df: Trade history
            balance: Current balance
            
        Returns:
            List of compliance violations
        """
        try:
            current_time = datetime.now()
            
            # Only check periodically
            if (current_time - self.last_check).total_seconds() < self.check_interval:
                return []
                
            self.last_check = current_time
            violations = []
            
            # Check position limits
            violations.extend(
                self._check_position_limits(positions, balance)
            )
            
            # Check trading frequency
            violations.extend(
                self._check_trading_frequency(trades_df)
            )
            
            # Check drawdown limits
            violations.extend(
                self._check_drawdown_limits(trades_df)
            )
            
            # Store violations
            self.violations.extend(violations)
            
            # Log violations
            for v in violations:
                logger.warning(
                    f"Compliance violation: {v['type']} - {v['description']}"
                )
                
            return violations
            
        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            return []
            
    def _check_position_limits(
        self,
        positions: Dict,
        balance: Decimal
    ) -> List[Dict]:
        """Check position size and count limits"""
        violations = []
        
        try:
            # Check maximum positions
            max_positions = self.config.get('max_positions', 5)
            if len(positions) > max_positions:
                violations.append({
                    'type': 'position_count',
                    'description': (
                        f"Position count {len(positions)} exceeds "
                        f"maximum {max_positions}"
                    ),
                    'timestamp': datetime.now().isoformat()
                })
                
            # Check position sizes
            max_position_size = Decimal(
                str(self.config.get('max_position_size', 0.2))
            )
            
            for pos_id, pos in positions.items():
                position_value = (
                    Decimal(str(pos['amount'])) *
                    Decimal(str(pos['current_price']))
                )
                position_size = position_value / balance
                
                if position_size > max_position_size:
                    violations.append({
                        'type': 'position_size',
                        'description': (
                            f"Position {pos_id} size {position_size:.2%} "
                            f"exceeds maximum {max_position_size:.2%}"
                        ),
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error checking position limits: {str(e)}")
            
        return violations
        
    def _check_trading_frequency(
        self,
        trades_df: pd.DataFrame
    ) -> List[Dict]:
        """Check trading frequency limits"""
        violations = []
        
        try:
            if len(trades_df) == 0:
                return violations
                
            # Check daily trade count
            max_daily_trades = self.config.get('max_daily_trades', 50)
            
            daily_trades = trades_df.groupby(
                pd.to_datetime(trades_df['timestamp']).dt.date
            ).size()
            
            if daily_trades.iloc[-1] > max_daily_trades:
                violations.append({
                    'type': 'trade_frequency',
                    'description': (
                        f"Daily trade count {daily_trades.iloc[-1]} "
                        f"exceeds maximum {max_daily_trades}"
                    ),
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error checking trading frequency: {str(e)}")
            
        return violations
        
    def _check_drawdown_limits(
        self,
        trades_df: pd.DataFrame
    ) -> List[Dict]:
        """Check drawdown limits"""
        violations = []
        
        try:
            if len(trades_df) == 0:
                return violations
                
            # Calculate drawdown
            returns = pd.to_numeric(trades_df['return'])
            cumulative_returns = returns.cumsum()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max)
            
            # Check maximum drawdown
            max_drawdown = self.config.get('max_drawdown', 0.2)
            current_drawdown = abs(float(drawdown.iloc[-1]))
            
            if current_drawdown > max_drawdown:
                violations.append({
                    'type': 'drawdown',
                    'description': (
                        f"Current drawdown {current_drawdown:.2%} "
                        f"exceeds maximum {max_drawdown:.2%}"
                    ),
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error checking drawdown limits: {str(e)}")
            
        return violations
        
    def get_violations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        violation_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get filtered compliance violations
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            violation_type: Optional violation type filter
            
        Returns:
            List of matching violations
        """
        filtered = self.violations
        
        if start_time:
            filtered = [
                v for v in filtered
                if datetime.fromisoformat(v['timestamp']) >= start_time
            ]
            
        if end_time:
            filtered = [
                v for v in filtered
                if datetime.fromisoformat(v['timestamp']) <= end_time
            ]
            
        if violation_type:
            filtered = [
                v for v in filtered
                if v['type'] == violation_type
            ]
            
        return filtered
