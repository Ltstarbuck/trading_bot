"""
External Bot Interface
Handles integration with external trading bots and their recommendations
"""

import asyncio
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import json
import websockets
from loguru import logger

class BotRecommendation:
    """Represents a trading recommendation from an external bot"""
    
    def __init__(
        self,
        symbol: str,
        action: str,
        source: str,
        confidence: float,
        timestamp: datetime,
        metadata: Optional[Dict] = None
    ):
        self.symbol = symbol
        self.action = action  # 'buy' or 'sell'
        self.source = source  # Name/ID of the recommending bot
        self.confidence = confidence  # 0.0 to 1.0
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.volatility: Optional[Decimal] = None
        self.current_price: Optional[Decimal] = None
        
    def to_dict(self) -> Dict:
        """Convert recommendation to dictionary"""
        return {
            'symbol': self.symbol,
            'action': self.action,
            'source': self.source,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'volatility': float(self.volatility) if self.volatility else None,
            'current_price': float(self.current_price) if self.current_price else None,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'BotRecommendation':
        """Create recommendation from dictionary"""
        return cls(
            symbol=data['symbol'],
            action=data['action'],
            source=data['source'],
            confidence=data['confidence'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )

class ExternalBotInterface:
    """Interface for managing external bot connections and recommendations"""
    
    def __init__(self):
        """Initialize bot interface"""
        self.recommendations: List[BotRecommendation] = []
        self.connected_bots: Dict[str, Dict] = {}
        self.websocket_clients: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._running = False
        
    async def start(self) -> None:
        """Start the bot interface"""
        self._running = True
        logger.info("Starting external bot interface")
        
    async def stop(self) -> None:
        """Stop the bot interface"""
        self._running = False
        # Close all websocket connections
        for ws in self.websocket_clients.values():
            await ws.close()
        self.websocket_clients.clear()
        logger.info("Stopped external bot interface")
        
    async def connect_bot(
        self,
        bot_id: str,
        connection_details: Dict
    ) -> bool:
        """
        Connect to an external bot
        
        Args:
            bot_id: Unique identifier for the bot
            connection_details: Connection configuration
            
        Returns:
            bool: True if connection successful
        """
        try:
            protocol = connection_details.get('protocol', 'ws')
            
            if protocol == 'ws':
                uri = connection_details['uri']
                timeout = connection_details.get('timeout', 30)  # 30 second default timeout
                ws = await asyncio.wait_for(
                    websockets.connect(uri),
                    timeout=timeout
                )
                self.websocket_clients[bot_id] = ws
                
                # Start listening for recommendations
                asyncio.create_task(self._listen_for_recommendations(bot_id, ws))
                
            self.connected_bots[bot_id] = connection_details
            logger.info(f"Connected to external bot: {bot_id}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to bot {bot_id}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to bot {bot_id}: {str(e)}")
            return False
            
    async def disconnect_bot(self, bot_id: str) -> None:
        """
        Disconnect from an external bot
        
        Args:
            bot_id: ID of bot to disconnect
        """
        if bot_id in self.websocket_clients:
            await self.websocket_clients[bot_id].close()
            del self.websocket_clients[bot_id]
            
        if bot_id in self.connected_bots:
            del self.connected_bots[bot_id]
            
        logger.info(f"Disconnected from bot: {bot_id}")
        
    def add_recommendation(self, recommendation: BotRecommendation) -> None:
        """
        Add a new recommendation
        
        Args:
            recommendation: Trading recommendation
        """
        self.recommendations.append(recommendation)
        self._clean_old_recommendations()
        logger.info(
            f"New recommendation from {recommendation.source}: "
            f"{recommendation.action} {recommendation.symbol}"
        )
        
    def get_recommendations(
        self,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        min_confidence: float = 0.0,
        max_age_minutes: int = 60
    ) -> List[BotRecommendation]:
        """
        Get filtered recommendations
        
        Args:
            symbol: Filter by symbol
            source: Filter by source bot
            min_confidence: Minimum confidence level
            max_age_minutes: Maximum age in minutes
            
        Returns:
            List of matching recommendations
        """
        current_time = datetime.now()
        filtered = []
        
        for rec in self.recommendations:
            # Check age
            age = (current_time - rec.timestamp).total_seconds() / 60
            if age > max_age_minutes:
                continue
                
            # Apply filters
            if symbol and rec.symbol != symbol:
                continue
            if source and rec.source != source:
                continue
            if rec.confidence < min_confidence:
                continue
                
            filtered.append(rec)
            
        return filtered
        
    def _clean_old_recommendations(self, max_age_minutes: int = 60) -> None:
        """Remove recommendations older than max_age_minutes"""
        current_time = datetime.now()
        self.recommendations = [
            rec for rec in self.recommendations
            if (current_time - rec.timestamp).total_seconds() / 60 <= max_age_minutes
        ]
        
    async def _listen_for_recommendations(
        self,
        bot_id: str,
        websocket: websockets.WebSocketClientProtocol
    ) -> None:
        """
        Listen for recommendations from a websocket connection
        
        Args:
            bot_id: ID of the connected bot
            websocket: WebSocket connection
        """
        try:
            while self._running:
                try:
                    message = await websocket.recv()
                    try:
                        data = json.loads(message)
                        
                        # Validate required fields
                        if not all(key in data for key in ['symbol', 'action']):
                            logger.warning(f"Invalid recommendation data from {bot_id}: {message}")
                            continue
                        
                        # Create recommendation from received data
                        recommendation = BotRecommendation(
                            symbol=data['symbol'],
                            action=data['action'],
                            source=bot_id,
                            confidence=data.get('confidence', 0.5),
                            timestamp=datetime.now(),
                            metadata=data.get('metadata')
                        )
                        
                        self.add_recommendation(recommendation)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from {bot_id}: {str(e)}")
                    except KeyError as e:
                        logger.error(f"Missing required field from {bot_id}: {str(e)}")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning(f"Connection closed for bot: {bot_id}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message from {bot_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in recommendation listener for {bot_id}: {str(e)}")
        finally:
            await self.disconnect_bot(bot_id)
