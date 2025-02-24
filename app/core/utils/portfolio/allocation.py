"""
Portfolio allocation utilities
"""

from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
import pandas as pd
from loguru import logger

@dataclass
class AssetAllocation:
    """Asset allocation data"""
    symbol: str
    weight: float
    target_value: float
    current_value: float
    rebalance_amount: float

class PortfolioAllocator:
    """Portfolio allocation manager"""
    
    def __init__(
        self,
        risk_free_rate: float = 0.02,
        rebalance_threshold: float = 0.05,
        min_weight: float = 0.05,
        max_weight: float = 0.40
    ):
        """
        Initialize allocator
        
        Args:
            risk_free_rate: Risk-free rate
            rebalance_threshold: Rebalance threshold
            min_weight: Minimum asset weight
            max_weight: Maximum asset weight
        """
        self.risk_free_rate = risk_free_rate
        self.rebalance_threshold = rebalance_threshold
        self.min_weight = min_weight
        self.max_weight = max_weight
        
    def calculate_equal_weight(
        self,
        portfolio_value: float,
        assets: List[str],
        current_values: Optional[Dict[str, float]] = None
    ) -> List[AssetAllocation]:
        """
        Calculate equal weight allocation
        
        Args:
            portfolio_value: Total portfolio value
            assets: Asset symbols
            current_values: Current asset values
            
        Returns:
            List of asset allocations
        """
        try:
            # Calculate weights
            weight = 1.0 / len(assets)
            target_value = portfolio_value * weight
            
            # Create allocations
            allocations = []
            for symbol in assets:
                current = current_values.get(symbol, 0.0) if current_values else 0.0
                rebalance = target_value - current
                
                allocations.append(
                    AssetAllocation(
                        symbol=symbol,
                        weight=weight,
                        target_value=target_value,
                        current_value=current,
                        rebalance_amount=rebalance
                    )
                )
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error calculating equal weight: {str(e)}")
            return []
            
    def calculate_market_cap_weight(
        self,
        portfolio_value: float,
        market_caps: Dict[str, float],
        current_values: Optional[Dict[str, float]] = None
    ) -> List[AssetAllocation]:
        """
        Calculate market cap weighted allocation
        
        Args:
            portfolio_value: Total portfolio value
            market_caps: Asset market caps
            current_values: Current asset values
            
        Returns:
            List of asset allocations
        """
        try:
            # Calculate total market cap
            total_mcap = sum(market_caps.values())
            
            # Calculate allocations
            allocations = []
            for symbol, mcap in market_caps.items():
                weight = mcap / total_mcap
                target_value = portfolio_value * weight
                current = current_values.get(symbol, 0.0) if current_values else 0.0
                rebalance = target_value - current
                
                allocations.append(
                    AssetAllocation(
                        symbol=symbol,
                        weight=weight,
                        target_value=target_value,
                        current_value=current,
                        rebalance_amount=rebalance
                    )
                )
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error calculating market cap weight: {str(e)}")
            return []
            
    def calculate_risk_parity(
        self,
        portfolio_value: float,
        returns: pd.DataFrame,
        current_values: Optional[Dict[str, float]] = None,
        target_risk: Optional[float] = None
    ) -> List[AssetAllocation]:
        """
        Calculate risk parity allocation
        
        Args:
            portfolio_value: Total portfolio value
            returns: Asset returns DataFrame
            current_values: Current asset values
            target_risk: Target portfolio risk
            
        Returns:
            List of asset allocations
        """
        try:
            # Calculate covariance matrix
            cov_matrix = returns.cov().values
            n_assets = len(returns.columns)
            
            # Define objective function
            def objective(weights):
                # Calculate asset contributions
                portfolio_risk = np.sqrt(
                    np.dot(weights.T, np.dot(cov_matrix, weights))
                )
                risk_contrib = weights * (np.dot(cov_matrix, weights)) / portfolio_risk
                
                # Minimize difference between contributions
                diff = risk_contrib - risk_contrib.mean()
                return np.sum(diff ** 2)
                
            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
            ]
            bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]
            
            # Initial guess
            initial_weights = np.array([1.0/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if not result.success:
                logger.warning("Risk parity optimization failed")
                return self.calculate_equal_weight(
                    portfolio_value,
                    returns.columns.tolist(),
                    current_values
                )
                
            # Create allocations
            allocations = []
            for i, symbol in enumerate(returns.columns):
                weight = float(result.x[i])
                target_value = portfolio_value * weight
                current = current_values.get(symbol, 0.0) if current_values else 0.0
                rebalance = target_value - current
                
                allocations.append(
                    AssetAllocation(
                        symbol=symbol,
                        weight=weight,
                        target_value=target_value,
                        current_value=current,
                        rebalance_amount=rebalance
                    )
                )
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error calculating risk parity: {str(e)}")
            return []
            
    def calculate_minimum_variance(
        self,
        portfolio_value: float,
        returns: pd.DataFrame,
        current_values: Optional[Dict[str, float]] = None
    ) -> List[AssetAllocation]:
        """
        Calculate minimum variance allocation
        
        Args:
            portfolio_value: Total portfolio value
            returns: Asset returns DataFrame
            current_values: Current asset values
            
        Returns:
            List of asset allocations
        """
        try:
            # Calculate covariance matrix
            cov_matrix = returns.cov().values
            n_assets = len(returns.columns)
            
            # Define objective function
            def objective(weights):
                return np.sqrt(
                    np.dot(weights.T, np.dot(cov_matrix, weights))
                )
                
            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
            ]
            bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]
            
            # Initial guess
            initial_weights = np.array([1.0/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if not result.success:
                logger.warning("Minimum variance optimization failed")
                return self.calculate_equal_weight(
                    portfolio_value,
                    returns.columns.tolist(),
                    current_values
                )
                
            # Create allocations
            allocations = []
            for i, symbol in enumerate(returns.columns):
                weight = float(result.x[i])
                target_value = portfolio_value * weight
                current = current_values.get(symbol, 0.0) if current_values else 0.0
                rebalance = target_value - current
                
                allocations.append(
                    AssetAllocation(
                        symbol=symbol,
                        weight=weight,
                        target_value=target_value,
                        current_value=current,
                        rebalance_amount=rebalance
                    )
                )
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error calculating minimum variance: {str(e)}")
            return []
            
    def calculate_maximum_sharpe(
        self,
        portfolio_value: float,
        returns: pd.DataFrame,
        expected_returns: Dict[str, float],
        current_values: Optional[Dict[str, float]] = None
    ) -> List[AssetAllocation]:
        """
        Calculate maximum Sharpe ratio allocation
        
        Args:
            portfolio_value: Total portfolio value
            returns: Asset returns DataFrame
            expected_returns: Expected asset returns
            current_values: Current asset values
            
        Returns:
            List of asset allocations
        """
        try:
            # Calculate covariance matrix
            cov_matrix = returns.cov().values
            n_assets = len(returns.columns)
            
            # Get expected returns array
            exp_returns = np.array([
                expected_returns[symbol]
                for symbol in returns.columns
            ])
            
            # Define objective function (negative Sharpe ratio)
            def objective(weights):
                portfolio_return = np.sum(weights * exp_returns)
                portfolio_risk = np.sqrt(
                    np.dot(weights.T, np.dot(cov_matrix, weights))
                )
                return -(portfolio_return - self.risk_free_rate) / portfolio_risk
                
            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
            ]
            bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]
            
            # Initial guess
            initial_weights = np.array([1.0/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if not result.success:
                logger.warning("Maximum Sharpe optimization failed")
                return self.calculate_equal_weight(
                    portfolio_value,
                    returns.columns.tolist(),
                    current_values
                )
                
            # Create allocations
            allocations = []
            for i, symbol in enumerate(returns.columns):
                weight = float(result.x[i])
                target_value = portfolio_value * weight
                current = current_values.get(symbol, 0.0) if current_values else 0.0
                rebalance = target_value - current
                
                allocations.append(
                    AssetAllocation(
                        symbol=symbol,
                        weight=weight,
                        target_value=target_value,
                        current_value=current,
                        rebalance_amount=rebalance
                    )
                )
                
            return allocations
            
        except Exception as e:
            logger.error(f"Error calculating maximum Sharpe: {str(e)}")
            return []
            
    def check_rebalance_needed(
        self,
        allocations: List[AssetAllocation]
    ) -> Tuple[bool, List[AssetAllocation]]:
        """
        Check if rebalancing is needed
        
        Args:
            allocations: Current allocations
            
        Returns:
            (rebalance_needed, rebalance_allocations)
        """
        try:
            # Calculate total value
            total_value = sum(a.current_value for a in allocations)
            
            # Check each allocation
            rebalance_needed = False
            for allocation in allocations:
                current_weight = allocation.current_value / total_value
                weight_diff = abs(current_weight - allocation.weight)
                
                if weight_diff > self.rebalance_threshold:
                    rebalance_needed = True
                    break
                    
            return rebalance_needed, allocations
            
        except Exception as e:
            logger.error(f"Error checking rebalance: {str(e)}")
            return False, allocations
            
    def calculate_rebalance_trades(
        self,
        allocations: List[AssetAllocation],
        prices: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate rebalance trades
        
        Args:
            allocations: Target allocations
            prices: Current asset prices
            
        Returns:
            Dictionary of symbol to trade amount
        """
        try:
            trades = {}
            
            for allocation in allocations:
                if allocation.rebalance_amount != 0:
                    price = prices.get(allocation.symbol)
                    if price:
                        quantity = allocation.rebalance_amount / price
                        trades[allocation.symbol] = quantity
                        
            return trades
            
        except Exception as e:
            logger.error(f"Error calculating rebalance trades: {str(e)}")
            return {}
