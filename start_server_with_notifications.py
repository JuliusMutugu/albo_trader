"""
Enhanced WebSocket Server with Desktop Notifications
Restart script to ensure notifications are enabled
"""

import asyncio
import signal
import sys
from enhanced_websocket_server import EnhancedWebSocketServer

async def main():
    """Main function to run the enhanced WebSocket server with notifications"""
    print("🚀 Starting Enigma-Apex Enhanced WebSocket Server with Desktop Notifications...")
    
    server = None
    
    def signal_handler(signum, frame):
        print("\n⚡ Shutdown signal received...")
        if server:
            asyncio.create_task(server.stop())
        sys.exit(0)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start enhanced server
        server = EnhancedWebSocketServer()
        await server.start()
        
        print("✅ Enhanced server started on ws://localhost:8765")
        print("🔔 Desktop notifications enabled!")
        print("📡 Ready for NinjaTrader connections with database integration!")
        print("💡 Send Enigma signals to see desktop notifications in action")
        print("\nPress Ctrl+C to stop the server...")
        
        # Keep server running
        while server.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⚡ Shutting down server...")
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if server:
            await server.stop()
            print("✅ Server stopped successfully")

if __name__ == "__main__":
    # Setup logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
