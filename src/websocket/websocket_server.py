"""
WebSocket Server - Real-time Communication Hub
Handles NinjaTrader dashboard, mobile app, and external connections
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Any, Callable
from dataclasses import asdict
import ssl
import uuid
from enum import Enum

class MessageType(Enum):
    """WebSocket message types"""
    ENIGMA_UPDATE = "enigma_update"
    KELLY_UPDATE = "kelly_update"
    CADENCE_UPDATE = "cadence_update"
    COMPLIANCE_UPDATE = "compliance_update"
    TRADE_SIGNAL = "trade_signal"
    EMERGENCY_STOP = "emergency_stop"
    HEARTBEAT = "heartbeat"
    STATUS_REQUEST = "status_request"
    CONFIG_UPDATE = "config_update"
    MOBILE_COMMAND = "mobile_command"
    ERROR = "error"

class ClientType(Enum):
    """Connected client types"""
    NINJA_DASHBOARD = "ninja_dashboard"
    MOBILE_APP = "mobile_app"
    EXTERNAL_API = "external_api"
    ADMIN_PANEL = "admin_panel"

class WebSocketMessage:
    """WebSocket message structure"""
    
    def __init__(self, 
                 message_type: MessageType,
                 data: Dict[str, Any],
                 client_id: str = None,
                 timestamp: datetime = None):
        
        self.message_type = message_type
        self.data = data
        self.client_id = client_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now()
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        try:
            # Ensure timestamp is valid
            timestamp_str = self.timestamp.isoformat() if self.timestamp else datetime.now().isoformat()
            
            return json.dumps({
                'type': self.message_type.value,
                'data': self.data,
                'client_id': self.client_id,
                'timestamp': timestamp_str
            })
        except Exception as e:
            # Fallback to basic message
            return json.dumps({
                'type': 'error',
                'data': {'error': f'Failed to serialize message: {str(e)}'},
                'client_id': self.client_id or 'unknown',
                'timestamp': datetime.now().isoformat()
            })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Create message from JSON string"""
        try:
            data = json.loads(json_str)
            
            # Handle different message type formats
            message_type_str = data.get('type', 'heartbeat')
            try:
                message_type = MessageType(message_type_str)
            except ValueError:
                # If message type not recognized, default to heartbeat
                message_type = MessageType.HEARTBEAT
            
            # Handle timestamp parsing
            timestamp = None
            if 'timestamp' in data:
                try:
                    if isinstance(data['timestamp'], str):
                        timestamp = datetime.fromisoformat(data['timestamp'])
                    elif isinstance(data['timestamp'], (int, float)):
                        timestamp = datetime.fromtimestamp(data['timestamp'])
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            
            return cls(
                message_type=message_type,
                data=data.get('data', {}),
                client_id=data.get('client_id'),
                timestamp=timestamp or datetime.now()
            )
        except Exception as e:
            # If parsing fails completely, create a basic heartbeat message
            return cls(
                message_type=MessageType.HEARTBEAT,
                data={'error': f'Failed to parse message: {str(e)}', 'original': json_str[:100]},
                client_id=None,
                timestamp=datetime.now()
            )

class ConnectedClient:
    """Connected WebSocket client information"""
    
    def __init__(self, 
                 websocket,
                 client_type: ClientType,
                 client_id: str,
                 user_agent: str = None):
        
        self.websocket = websocket
        self.client_type = client_type
        self.client_id = client_id
        self.user_agent = user_agent
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.message_count = 0

class WebSocketServer:
    """
    Real-time WebSocket communication server
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 8765,
                 ssl_cert_path: str = None,
                 ssl_key_path: str = None):
        
        self.logger = logging.getLogger(__name__)
        
        # Server configuration
        self.host = host
        self.port = port
        self.ssl_cert_path = ssl_cert_path
        self.ssl_key_path = ssl_key_path
        
        # Connected clients
        self.clients: Dict[str, ConnectedClient] = {}
        self.clients_by_type: Dict[ClientType, Set[str]] = {
            client_type: set() for client_type in ClientType
        }
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Server state
        self.running = False
        self.server = None
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'start_time': None,
            'last_activity': None
        }
        
        # Setup default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.STATUS_REQUEST] = self._handle_status_request
        self.message_handlers[MessageType.MOBILE_COMMAND] = self._handle_mobile_command
    
    async def start(self):
        """Start the WebSocket server"""
        try:
            # Setup SSL context if certificates provided
            ssl_context = None
            if self.ssl_cert_path and self.ssl_key_path:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(self.ssl_cert_path, self.ssl_key_path)
                self.logger.info("SSL enabled for WebSocket server")
            
            # Start server
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            protocol = "wss" if ssl_context else "ws"
            self.logger.info(f"WebSocket server started on {protocol}://{self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Close all client connections
        for client in self.clients.values():
            await client.websocket.close()
        
        self.clients.clear()
        self.clients_by_type = {client_type: set() for client_type in ClientType}
        
        self.logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket):
        """Handle new client connection"""
        # Get path from websocket request
        path = websocket.path if hasattr(websocket, 'path') else '/'
        
        client_id = str(uuid.uuid4())
        client_type = self._determine_client_type(path)
        
        try:
            # Create client record
            client = ConnectedClient(
                websocket=websocket,
                client_type=client_type,
                client_id=client_id,
                user_agent=getattr(websocket, 'request_headers', {}).get('User-Agent', 'Unknown')
            )
            
            # Add to client tracking
            self.clients[client_id] = client
            self.clients_by_type[client_type].add(client_id)
            self.stats['total_connections'] += 1
            
            self.logger.info(f"New {client_type.value} client connected: {client_id}")
            
            # Send welcome message
            welcome_msg = WebSocketMessage(
                MessageType.STATUS_REQUEST,
                {
                    'client_id': client_id,
                    'client_type': client_type.value,
                    'server_time': datetime.now().isoformat(),
                    'status': 'connected',
                    'welcome': True,
                    'server_status': 'running',
                    'enigma_data': {
                        'power_score': 0,
                        'confluence_level': 'L1', 
                        'signal_color': 'NEUTRAL',
                        'macvu_state': 'NEUTRAL'
                    }
                }
            )
            await self._send_to_client(client_id, welcome_msg)
            
            # Handle messages from this client
            async for message in websocket:
                await self._process_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self._remove_client(client_id)
    
    def _determine_client_type(self, path: str) -> ClientType:
        """Determine client type from connection path"""
        if '/ninja' in path:
            return ClientType.NINJA_DASHBOARD
        elif '/mobile' in path:
            return ClientType.MOBILE_APP
        elif '/admin' in path:
            return ClientType.ADMIN_PANEL
        else:
            return ClientType.EXTERNAL_API
    
    async def _process_message(self, client_id: str, raw_message: str):
        """Process incoming message from client"""
        try:
            print(f"DEBUG: Processing message from {client_id}: {raw_message[:100]}...")
            
            message = WebSocketMessage.from_json(raw_message)
            message.client_id = client_id
            
            self.stats['messages_received'] += 1
            self.stats['last_activity'] = datetime.now()
            
            # Update client heartbeat
            if client_id in self.clients:
                self.clients[client_id].last_heartbeat = datetime.now()
                self.clients[client_id].message_count += 1
            
            print(f"DEBUG: Message type: {message.message_type.value}")
            
            # Route message to appropriate handler
            if message.message_type in self.message_handlers:
                print(f"DEBUG: Calling handler for {message.message_type.value}")
                await self.message_handlers[message.message_type](client_id, message)
                print(f"DEBUG: Handler completed for {message.message_type.value}")
            else:
                self.logger.warning(f"No handler for message type: {message.message_type.value}")
                print(f"DEBUG: No handler for message type: {message.message_type.value}")
                
        except Exception as e:
            self.logger.error(f"Error processing message from {client_id}: {e}")
            print(f"DEBUG: Error in _process_message: {e}")
            import traceback
            traceback.print_exc()
            
            # Send error response
            try:
                error_msg = WebSocketMessage(
                    MessageType.ERROR,
                    {'error': str(e), 'original_message': raw_message[:100]}
                )
                await self._send_to_client(client_id, error_msg)
            except Exception as send_error:
                print(f"DEBUG: Failed to send error message: {send_error}")
    
    async def _handle_heartbeat(self, client_id: str, message: WebSocketMessage):
        """Handle heartbeat message"""
        if client_id in self.clients:
            self.clients[client_id].last_heartbeat = datetime.now()
            
        # Send heartbeat response
        response = WebSocketMessage(
            MessageType.HEARTBEAT,
            {
                'server_time': datetime.now().isoformat(),
                'client_id': client_id
            }
        )
        await self._send_to_client(client_id, response)
    
    async def _handle_status_request(self, client_id: str, message: WebSocketMessage):
        """Handle status request"""
        try:
            status_data = {
                'server_status': 'running' if self.running else 'stopped',
                'connected_clients': len(self.clients),
                'client_types': {
                    client_type.value: len(client_ids) 
                    for client_type, client_ids in self.clients_by_type.items()
                },
                'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0,
                'statistics': {
                    'total_connections': self.stats.get('total_connections', 0),
                    'messages_sent': self.stats.get('messages_sent', 0),
                    'messages_received': self.stats.get('messages_received', 0),
                    'last_activity': self.stats.get('last_activity', datetime.now()).isoformat() if self.stats.get('last_activity') else None
                },
                'enigma_data': {
                    'power_score': 0,
                    'confluence_level': 'L1', 
                    'signal_color': 'NEUTRAL',
                    'macvu_state': 'NEUTRAL'
                }
            }
            
            response = WebSocketMessage(
                MessageType.STATUS_REQUEST,
                status_data
            )
            await self._send_to_client(client_id, response)
            
        except Exception as e:
            self.logger.error(f"Error handling status request: {e}")
            # Send simple error response
            error_response = WebSocketMessage(
                MessageType.ERROR,
                {'error': 'Failed to get status', 'details': str(e)}
            )
            await self._send_to_client(client_id, error_response)
    
    async def _handle_mobile_command(self, client_id: str, message: WebSocketMessage):
        """Handle mobile app commands"""
        command = message.data.get('command')
        
        if command == 'emergency_stop':
            # Broadcast emergency stop to all clients
            await self.broadcast_emergency_stop(
                reason=message.data.get('reason', 'Mobile app emergency stop'),
                triggered_by=client_id
            )
        
        elif command == 'get_status':
            # Send current system status
            await self._handle_status_request(client_id, message)
        
        else:
            self.logger.warning(f"Unknown mobile command: {command}")
    
    async def _send_to_client(self, client_id: str, message: WebSocketMessage):
        """Send message to specific client"""
        if client_id not in self.clients:
            self.logger.warning(f"Attempted to send message to unknown client: {client_id}")
            return
        
        try:
            print(f"DEBUG: Sending message to {client_id}: {message.message_type.value}")
            client = self.clients[client_id]
            
            # Generate JSON first to catch any serialization errors
            json_data = message.to_json()
            print(f"DEBUG: JSON length: {len(json_data)}")
            
            await client.websocket.send(json_data)
            self.stats['messages_sent'] += 1
            print(f"DEBUG: Message sent successfully to {client_id}")
            
        except websockets.exceptions.ConnectionClosed:
            print(f"DEBUG: Connection closed for {client_id}")
            await self._remove_client(client_id)
        except Exception as e:
            self.logger.error(f"Error sending message to client {client_id}: {e}")
            print(f"DEBUG: Error in _send_to_client: {e}")
            import traceback
            traceback.print_exc()
            await self._remove_client(client_id)
    
    async def _remove_client(self, client_id: str):
        """Remove client from tracking"""
        if client_id in self.clients:
            client = self.clients[client_id]
            self.clients_by_type[client.client_type].discard(client_id)
            del self.clients[client_id]
            
            self.logger.info(f"Removed client: {client_id}")
    
    async def broadcast_to_type(self, client_type: ClientType, message: WebSocketMessage):
        """Broadcast message to all clients of specific type"""
        client_ids = self.clients_by_type[client_type].copy()
        
        for client_id in client_ids:
            await self._send_to_client(client_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        client_ids = list(self.clients.keys())
        
        for client_id in client_ids:
            await self._send_to_client(client_id, message)
    
    async def send_enigma_update(self, enigma_data: Dict[str, Any]):
        """Send Enigma panel update to relevant clients"""
        message = WebSocketMessage(
            MessageType.ENIGMA_UPDATE,
            {
                'enigma_data': enigma_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Send to NinjaTrader dashboard and mobile apps
        await self.broadcast_to_type(ClientType.NINJA_DASHBOARD, message)
        await self.broadcast_to_type(ClientType.MOBILE_APP, message)
    
    async def send_kelly_update(self, kelly_data: Dict[str, Any]):
        """Send Kelly position sizing update"""
        message = WebSocketMessage(
            MessageType.KELLY_UPDATE,
            {
                'kelly_data': kelly_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        await self.broadcast_to_type(ClientType.NINJA_DASHBOARD, message)
        await self.broadcast_to_type(ClientType.MOBILE_APP, message)
    
    async def send_cadence_update(self, cadence_data: Dict[str, Any]):
        """Send Cadence tracking update"""
        message = WebSocketMessage(
            MessageType.CADENCE_UPDATE,
            {
                'cadence_data': cadence_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        await self.broadcast_to_type(ClientType.NINJA_DASHBOARD, message)
        await self.broadcast_to_type(ClientType.MOBILE_APP, message)
    
    async def send_compliance_update(self, compliance_data: Dict[str, Any]):
        """Send Compliance monitoring update"""
        message = WebSocketMessage(
            MessageType.COMPLIANCE_UPDATE,
            {
                'compliance_data': compliance_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        await self.broadcast_to_type(ClientType.NINJA_DASHBOARD, message)
        await self.broadcast_to_type(ClientType.MOBILE_APP, message)
    
    async def send_trade_signal(self, signal_data: Dict[str, Any]):
        """Send trade signal to NinjaTrader"""
        message = WebSocketMessage(
            MessageType.TRADE_SIGNAL,
            {
                'signal_data': signal_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Send primarily to NinjaTrader dashboard
        await self.broadcast_to_type(ClientType.NINJA_DASHBOARD, message)
        
        # Also send to mobile for monitoring
        await self.broadcast_to_type(ClientType.MOBILE_APP, message)
    
    async def broadcast_emergency_stop(self, reason: str, triggered_by: str = None):
        """Broadcast emergency stop to all clients"""
        message = WebSocketMessage(
            MessageType.EMERGENCY_STOP,
            {
                'reason': reason,
                'triggered_by': triggered_by,
                'timestamp': datetime.now().isoformat(),
                'action_required': 'stop_all_trading'
            }
        )
        
        await self.broadcast_to_all(message)
        self.logger.critical(f"Emergency stop broadcasted: {reason}")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register custom message handler"""
        self.message_handlers[message_type] = handler
    
    def get_connected_clients(self) -> Dict[str, Dict]:
        """Get information about connected clients"""
        return {
            client_id: {
                'client_type': client.client_type.value,
                'connected_at': client.connected_at.isoformat(),
                'last_heartbeat': client.last_heartbeat.isoformat(),
                'message_count': client.message_count,
                'user_agent': client.user_agent
            }
            for client_id, client in self.clients.items()
        }
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 5):
        """Remove stale connections that haven't sent heartbeat"""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        stale_clients = []
        
        for client_id, client in self.clients.items():
            if client.last_heartbeat < cutoff_time:
                stale_clients.append(client_id)
        
        for client_id in stale_clients:
            await self._remove_client(client_id)
            self.logger.info(f"Removed stale client: {client_id}")
    
    def is_healthy(self) -> bool:
        """Check if WebSocket server is healthy"""
        return self.running and self.server is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket server statistics"""
        return {
            **self.stats,
            'running': self.running,
            'connected_clients': len(self.clients),
            'clients_by_type': {
                client_type.value: len(client_ids) 
                for client_type, client_ids in self.clients_by_type.items()
            },
            'is_healthy': self.is_healthy()
        }

# Main execution
if __name__ == "__main__":
    import sys
    import traceback
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        """Main server execution"""
        try:
            print("🚀 Starting Enigma-Apex WebSocket Server...")
            server = WebSocketServer()
            
            print("✅ Server created successfully")
            await server.start()
            
            print("✅ Server started on ws://localhost:8765")
            print("📡 Ready for NinjaTrader connections!")
            
            # Keep running until interrupted
            try:
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                print("\n🛑 Shutting down server...")
                await server.stop()
                print("✅ Server stopped")
                
        except Exception as e:
            print(f"❌ Server error: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        traceback.print_exc()
        sys.exit(1)
