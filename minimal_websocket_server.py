"""
Minimal WebSocket Server for Testing
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_client(websocket):
    """Handle client connections"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        async for message in websocket:
            logger.info(f"Received from {client_id}: {message}")
            
            try:
                # Parse message
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Create response
                response = {
                    'type': msg_type + '_response',
                    'data': {
                        'status': 'received',
                        'timestamp': datetime.now().isoformat(),
                        'original_type': msg_type
                    },
                    'client_id': str(client_id)
                }
                
                # Send response
                await websocket.send(json.dumps(response))
                logger.info(f"Sent response to {client_id}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message}")
                error_response = {
                    'type': 'error',
                    'data': {'error': 'Invalid JSON'},
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(error_response))
                
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                traceback.print_exc()
                
                error_response = {
                    'type': 'error', 
                    'data': {'error': str(e)},
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(error_response))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        traceback.print_exc()

async def main():
    """Start the WebSocket server"""
    logger.info("Starting minimal WebSocket server on localhost:8765")
    
    try:
        async with websockets.serve(handle_client, "localhost", 8765):
            logger.info("✅ Server started successfully")
            
            # Keep running
            await asyncio.Future()  # Run forever
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        traceback.print_exc()
