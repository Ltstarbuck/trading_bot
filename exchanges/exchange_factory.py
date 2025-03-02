"""
Exchange Factory
Creates and manages exchange instances
"""

from typing import Dict, Optional
from loguru import logger

from .base_exchange import BaseExchange
from .binance import BinanceExchange
from .kraken import KrakenExchange

class ExchangeFactory:
    """Factory for creating exchange instances"""
    
    def __init__(self):
        """Initialize the factory"""
        self._exchanges: Dict[str, BaseExchange] = {}
        self._exchange_classes = {
            'binance': BinanceExchange,
            'kraken': KrakenExchange,
        }
        
    def create_exchange(
        self,
        exchange_id: str,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = False
    ) -> Optional[BaseExchange]:
        """
        Create or retrieve an exchange instance
        
        Args:
            exchange_id: Identifier for the exchange
            api_key: API key for authentication
            api_secret: API secret for authentication
            testnet: Whether to use testnet/sandbox
            
        Returns:
            Exchange instance or None if exchange_id is invalid
        """
        try:
            if exchange_id not in self._exchanges:
                if exchange_id not in self._exchange_classes:
                    logger.error(f"Unsupported exchange: {exchange_id}")
                    return None
                    
                exchange_class = self._exchange_classes[exchange_id]
                self._exchanges[exchange_id] = exchange_class(
                    api_key=api_key,
                    api_secret=api_secret,
                    testnet=testnet
                )
                logger.info(f"Created new {exchange_id} exchange instance")
                
            return self._exchanges[exchange_id]
            
        except Exception as e:
            logger.error(f"Error creating exchange {exchange_id}: {str(e)}")
            return None
            
    def get_exchange(self, exchange_id: str) -> Optional[BaseExchange]:
        """
        Get an existing exchange instance
        
        Args:
            exchange_id: Identifier for the exchange
            
        Returns:
            Exchange instance or None if not found
        """
        return self._exchanges.get(exchange_id)
        
    def get_available_exchanges(self) -> list:
        """
        Get list of supported exchanges
        
        Returns:
            List of exchange identifiers
        """
        return list(self._exchange_classes.keys())
        
    def remove_exchange(self, exchange_id: str) -> None:
        """
        Remove an exchange instance
        
        Args:
            exchange_id: Identifier for the exchange to remove
        """
        if exchange_id in self._exchanges:
            del self._exchanges[exchange_id]
            logger.info(f"Removed exchange instance: {exchange_id}")
            
    def clear_exchanges(self) -> None:
        """Remove all exchange instances"""
        self._exchanges.clear()
        logger.info("Cleared all exchange instances")
