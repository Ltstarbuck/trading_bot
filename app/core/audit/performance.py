"""
Performance tracking module
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

class PerformanceTracker:
    """Tracks trading performance metrics"""
    
    def __init__(self):
        """Initialize performance tracker"""
        self.trades_df: Optional[pd.DataFrame] = None
        self.metrics: Dict = {}
        
    def update_trades(self, trades_df: pd.DataFrame) -> None:
        """
        Update trade data
        
        Args:
            trades_df: DataFrame of trades
        """
        try:
            self.trades_df = trades_df.copy()
            
            # Convert timestamps
            self.trades_df['timestamp'] = pd.to_datetime(
                self.trades_df['timestamp']
            )
            
            # Convert numeric columns
            numeric_cols = ['amount', 'price', 'fees']
            for col in numeric_cols:
                if col in self.trades_df:
                    self.trades_df[col] = pd.to_numeric(
                        self.trades_df[col]
                    )
                    
            # Calculate trade values
            self.trades_df['value'] = (
                self.trades_df['amount'] * self.trades_df['price']
            )
            
            # Calculate returns
            self._calculate_returns()
            
        except Exception as e:
            logger.error(f"Error updating trades: {str(e)}")
            
    def calculate_metrics(
        self,
        initial_balance: Decimal,
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Calculate performance metrics
        
        Args:
            initial_balance: Starting balance
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary of metrics
        """
        try:
            if self.trades_df is None or len(self.trades_df) == 0:
                return {}
                
            # Basic metrics
            self.metrics['total_trades'] = len(self.trades_df)
            self.metrics['winning_trades'] = len(
                self.trades_df[self.trades_df['return'] > 0]
            )
            self.metrics['losing_trades'] = len(
                self.trades_df[self.trades_df['return'] < 0]
            )
            
            # Win rate
            self.metrics['win_rate'] = (
                self.metrics['winning_trades'] / self.metrics['total_trades']
            )
            
            # Profit metrics
            self.metrics['total_profit'] = float(
                self.trades_df['return'].sum()
            )
            self.metrics['average_profit'] = float(
                self.trades_df['return'].mean()
            )
            
            # Risk metrics
            returns = self.trades_df['return'].values
            self.metrics['volatility'] = float(np.std(returns))
            self.metrics['max_drawdown'] = self._calculate_max_drawdown()
            
            # Risk-adjusted returns
            self.metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(
                risk_free_rate
            )
            self.metrics['sortino_ratio'] = self._calculate_sortino_ratio(
                risk_free_rate
            )
            
            # Calculate equity curve
            self.metrics['equity_curve'] = self._calculate_equity_curve(
                initial_balance
            )
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
            
    def get_daily_returns(self) -> pd.Series:
        """Calculate daily returns"""
        if self.trades_df is None:
            return pd.Series()
            
        daily_returns = self.trades_df.groupby(
            self.trades_df['timestamp'].dt.date
        )['return'].sum()
        
        return daily_returns
        
    def _calculate_returns(self) -> None:
        """Calculate trade returns"""
        self.trades_df['return'] = self.trades_df.apply(
            lambda row: (
                row['value'] * (1 if row['side'] == 'buy' else -1)
            ),
            axis=1
        )
        
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if self.trades_df is None:
            return 0.0
            
        cumulative_returns = self.trades_df['return'].cumsum()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns - rolling_max
        return float(abs(drawdowns.min()))
        
    def _calculate_sharpe_ratio(
        self,
        risk_free_rate: float
    ) -> float:
        """Calculate Sharpe ratio"""
        if self.trades_df is None:
            return 0.0
            
        returns = self.trades_df['return'].values
        excess_returns = np.mean(returns) - risk_free_rate
        return float(
            excess_returns / np.std(returns)
            if np.std(returns) > 0
            else 0.0
        )
        
    def _calculate_sortino_ratio(
        self,
        risk_free_rate: float
    ) -> float:
        """Calculate Sortino ratio"""
        if self.trades_df is None:
            return 0.0
            
        returns = self.trades_df['return'].values
        excess_returns = np.mean(returns) - risk_free_rate
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns)
        
        return float(
            excess_returns / downside_std
            if downside_std > 0
            else 0.0
        )
        
    def _calculate_equity_curve(
        self,
        initial_balance: Decimal
    ) -> pd.Series:
        """Calculate equity curve"""
        if self.trades_df is None:
            return pd.Series()
            
        returns = self.trades_df['return'].values
        cumulative_returns = np.cumsum(returns)
        equity_curve = initial_balance * (1 + cumulative_returns)
        
        return pd.Series(
            equity_curve,
            index=self.trades_df['timestamp']
        )
