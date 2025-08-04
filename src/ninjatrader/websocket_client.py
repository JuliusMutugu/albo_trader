"""
NinjaTrader WebSocket client for real-time communication.

This module handles bidirectional communication with NinjaTrader 8
for order execution and market data.
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class NinjaTraderClient:
    """
    WebSocket client for NinjaTrader 8 communication.
    
    Features:
    - Order execution
    - Position monitoring
    - Account status updates
    - Market data subscription
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection settings
        self.host = config.get('websocket_host', 'localhost')
        self.port = config.get('websocket_port', 8080)
        self.reconnect_delay = config.get('reconnect_delay', 5.0)
        
        # Connection state
        self.websocket = None
        self.is_connected = False
        self.is_running = False
        
        # Message callbacks
        self.message_handlers = {}
        
    async def start(self):
        """Start the WebSocket client."""
        try:
            self.logger.info("Starting NinjaTrader WebSocket client...")
            self.is_running = True
            
            while self.is_running:
                try:
                    await self._connect()
                    await self._handle_messages()
                except Exception as e:
                    self.logger.error(f"Connection error: {e}")
                    self.is_connected = False
                    
                    if self.is_running:
                        self.logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                        await asyncio.sleep(self.reconnect_delay)
                        
        except Exception as e:
            self.logger.error(f"Client startup error: {e}")
            
    async def shutdown(self):
        """Shutdown the WebSocket client."""
        self.logger.info("Shutting down NinjaTrader WebSocket client...")
        self.is_running = False
        
        if self.websocket:
            await self.websocket.close()
            
    async def _connect(self):
        """Establish WebSocket connection to NinjaTrader."""
        try:
            uri = f"ws://{self.host}:{self.port}"
            self.logger.info(f"Connecting to NinjaTrader at {uri}")
            
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            
            self.logger.info("Connected to NinjaTrader WebSocket")
            
            # Send initial handshake
            await self._send_handshake()
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise
            
    async def _send_handshake(self):
        """Send initial handshake message."""
        handshake = {
            "type": "handshake",
            "client_id": "enigma_apex_panel",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_message(handshake)
        
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    self.logger.error(f"Message processing error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Message handling error: {e}")
            self.is_connected = False
            
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message from NinjaTrader."""
        try:
            message_type = data.get('type')
            
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(data)
            else:
                self.logger.debug(f"Unhandled message type: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
            
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to NinjaTrader."""
        try:
            if not self.is_connected or not self.websocket:
                raise ConnectionError("Not connected to NinjaTrader")
                
            json_message = json.dumps(message)
            await self.websocket.send(json_message)
            
            self.logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Message send error: {e}")
            raise
            
    async def send_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Send order to NinjaTrader.
        
        Args:
            order_data: Order information from Guardian Engine
            
        Returns:
            True if order was sent successfully
        """
        try:
            order_message = {
                "type": "place_order",
                "order": {
                    "instrument": "ES 03-25",  # Example: E-mini S&P 500
                    "action": "BUY" if order_data['direction'] == 'long' else "SELL",
                    "quantity": order_data['position_size'],
                    "order_type": "MARKET",
                    "stop_loss": order_data.get('stop_loss'),
                    "profit_target": order_data.get('profit_target'),
                    "time_in_force": "DAY"
                },
                "timestamp": datetime.now().isoformat(),
                "client_order_id": f"EA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            await self._send_message(order_message)
            
            self.logger.info(f"Order sent: {order_data['direction']} {order_data['position_size']} contracts")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Order send error: {e}")
            return False
            
    async def close_position(self) -> bool:
        """
        Close current position.
        
        Returns:
            True if close order was sent successfully
        """
        try:
            close_message = {
                "type": "close_position",
                "instrument": "ES 03-25",
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_message(close_message)
            
            self.logger.info("Position close order sent")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Position close error: {e}")
            return False
            
    async def request_account_info(self) -> bool:
        """
        Request account information from NinjaTrader.
        
        Returns:
            True if request was sent successfully
        """
        try:
            request_message = {
                "type": "account_info_request",
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_message(request_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Account info request error: {e}")
            return False
            
    async def subscribe_to_market_data(self, instruments: list) -> bool:
        """
        Subscribe to market data for specified instruments.
        
        Args:
            instruments: List of instruments to subscribe to
            
        Returns:
            True if subscription was successful
        """
        try:
            subscription_message = {
                "type": "market_data_subscribe",
                "instruments": instruments,
                "data_types": ["LAST", "BID", "ASK", "VOLUME"],
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_message(subscription_message)
            
            self.logger.info(f"Subscribed to market data: {instruments}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Market data subscription error: {e}")
            return False
            
    def register_message_handler(self, message_type: str, handler: Callable):
        """
        Register handler for specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for message type: {message_type}")
        
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status.
        
        Returns:
            Dictionary with connection information
        """
        return {
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "handlers_registered": len(self.message_handlers)
        }
