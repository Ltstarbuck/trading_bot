"""
Base class for technical indicators
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger

class BaseIndicator(ABC):
    """Abstract base class for technical indicators"""
    
    def __init__(self, name: str):
        """
        Initialize base indicator
        
        Args:
            name: Indicator name
        """
        self.name = name
        
    @abstractmethod
    def calculate(
        self,
        data: pd.DataFrame,
        **kwargs
    ) -> pd.DataFrame:
        """
        Calculate indicator values
        
        Args:
            data: OHLCV DataFrame
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with indicator values
        """
        pass
        
    def validate_data(
        self,
        data: pd.DataFrame,
        required_columns: List[str]
    ) -> bool:
        """
        Validate input data
        
        Args:
            data: Input DataFrame
            required_columns: Required column names
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if DataFrame is empty
            if data.empty:
                logger.warning(f"{self.name}: Empty DataFrame provided")
                return False
                
            # Check required columns
            missing_cols = [
                col for col in required_columns
                if col not in data.columns
            ]
            
            if missing_cols:
                logger.warning(
                    f"{self.name}: Missing required columns: {missing_cols}"
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(
                f"{self.name}: Error validating data: {str(e)}"
            )
            return False
            
    def prepare_output(
        self,
        data: pd.DataFrame,
        indicator_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prepare output DataFrame
        
        Args:
            data: Original DataFrame
            indicator_data: Calculated indicator values
            
        Returns:
            Combined DataFrame
        """
        try:
            # Create copy of original data
            output = data.copy()
            
            # Add indicator columns
            for column in indicator_data.columns:
                output[f"{self.name}_{column}"] = indicator_data[column]
                
            return output
            
        except Exception as e:
            logger.error(
                f"{self.name}: Error preparing output: {str(e)}"
            )
            return data
