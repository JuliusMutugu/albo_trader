"""
Simple WebSocket Server Test
Direct test to identify WebSocket issues
"""

import asyncio
import websockets
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def echo_server(websocket):
    """Simple echo server for testing"""
    path = getattr(websocket, 'path', '/')
    logger.info(f"New connection from {websocket.remote_address} on path {path}")
    
    try:
        async for message in websocket:
            logger.info(f"Received: {message}")
            
            try:
                # Try to parse as JSON
                data = json.loads(message)
                
                # Create response
                response = {
                    "type": "response",
                    "original": data,
                    "server_message": "Echo from Enigma-Apex WebSocket",
                    "path": path
                }
                
                response_json = json.dumps(response)
                await websocket.send(response_json)
                logger.info(f"Sent: {response_json}")
                
            except json.JSONDecodeError:
                # Not JSON, just echo back
                await websocket.send(f"Echo: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in echo server: {e}")

async def start_test_server():
    """Start the test WebSocket server"""
    logger.info("Starting test WebSocket server on localhost:8766...")
    
    server = await websockets.serve(echo_server, "localhost", 8766)
    logger.info("Test server started successfully!")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

async def test_simple_client():
    """Test client to connect to our simple server"""
    logger.info("Testing simple WebSocket client...")
    
    try:
        async with websockets.connect('ws://localhost:8766') as websocket:
            logger.info("Connected to test server!")
            
            # Send test message
            test_message = {
                "type": "test",
                "data": {"message": "Hello from test client"}
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            return True
            
    except Exception as e:
        logger.error(f"Test client error: {e}")
        return False

async def main():
    """Run both server and client test"""
    print("🔧 WebSocket Simple Test")
    print("=" * 40)
    
    # Start server in background
    server_task = asyncio.create_task(start_test_server())
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    # Test client connection
    client_success = await test_simple_client()
    
    if client_success:
        print("✅ Simple WebSocket test passed!")
        print("   The issue is likely in the Enigma-Apex WebSocket implementation")
    else:
        print("❌ Simple WebSocket test failed!")
        print("   There may be a more fundamental WebSocket issue")
    
    # Cancel server
    server_task.cancel()
    
    print("\nPress Ctrl+C to continue...")

if __name__ == "__main__":
    asyncio.run(main())
