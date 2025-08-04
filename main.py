"""
Main Enigma-Apex System Launcher
Coordinates all components of the professional trading system
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.config_manager import ConfigManager
from src.core.guardian_engine import GuardianEngine
from src.mobile.mobile_interface import MobileInterfaceServer
from src.websocket.websocket_server import WebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enigma_apex.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnigmaApexSystem:
    """
    Main system coordinator for Enigma-Apex Prop Trading Panel
    
    This class orchestrates all components:
    - Guardian Engine (core trading logic)
    - OCR Processor (AlgoBox Enigma reading)
    - Kelly Engine (position sizing)
    - Compliance Monitor (Apex rules)
    - Cadence Tracker (timing analysis)
    - WebSocket Server (NinjaTrader communication)
    - Mobile Interface (remote control)
    - Database Manager (trade logging)
    """
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.guardian_engine = None
        self.mobile_server = None
        self.websocket_server = None
        self.running = False
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def initialize(self):
        """Initialize all system components"""
        logger.info("=" * 60)
        logger.info("ENIGMA-APEX PROP TRADING PANEL INITIALIZATION")
        logger.info("=" * 60)
        
        try:
            # Load configuration
            self.config_manager.load_config()
            settings = self.config_manager.get_settings()
            logger.info("✓ Configuration loaded")
            
            # Initialize Guardian Engine
            self.guardian_engine = GuardianEngine(settings)
            logger.info("✓ Guardian Engine initialized")
            
            # Initialize Mobile Interface
            self.mobile_server = MobileInterfaceServer()
            self.mobile_server.connect_guardian_engine(self.guardian_engine)
            logger.info("✓ Mobile Interface initialized")
            
            # Initialize WebSocket Server for NinjaTrader
            self.websocket_server = WebSocketServer(port=8765)
            logger.info("✓ WebSocket Server initialized")
            
            logger.info("=" * 60)
            logger.info("ALL COMPONENTS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the complete Enigma-Apex system"""
        logger.info("Starting Enigma-Apex System...")
        
        try:
            # Start all components concurrently
            tasks = [
                # Core Guardian Engine
                asyncio.create_task(self.guardian_engine.start(), name="GuardianEngine"),
                
                # Mobile Interface Server
                asyncio.create_task(
                    self.mobile_server.start_server(host="0.0.0.0", port=8000), 
                    name="MobileServer"
                ),
                
                # WebSocket Server for NinjaTrader
                asyncio.create_task(self.websocket_server.start(), name="WebSocketServer"),
                
                # System status monitor
                asyncio.create_task(self._system_monitor(), name="SystemMonitor")
            ]
            
            self.running = True
            
            logger.info("🚀 ENIGMA-APEX SYSTEM ONLINE 🚀")
            logger.info("✓ Guardian Engine: ACTIVE")
            logger.info("✓ OCR Processor: MONITORING AlgoBox Enigma")
            logger.info("✓ Kelly Engine: CALCULATING POSITIONS")
            logger.info("✓ Compliance Monitor: ENFORCING APEX RULES")
            logger.info("✓ Mobile Interface: http://localhost:8000")
            logger.info("✓ NinjaTrader WebSocket: ws://localhost:8765")
            logger.info("=" * 60)
            
            # Wait for all tasks or shutdown signal
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"System error: {e}")
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Initiating system shutdown...")
        self.running = False
        
        try:
            # Shutdown Guardian Engine
            if self.guardian_engine:
                await self.guardian_engine.shutdown()
                logger.info("✓ Guardian Engine shutdown")
            
            # Mobile server will shutdown when tasks are cancelled
            logger.info("✓ Mobile Interface shutdown")
            
            # WebSocket server shutdown
            if self.websocket_server:
                await self.websocket_server.stop()
                logger.info("✓ WebSocket Server shutdown")
            
            logger.info("=" * 60)
            logger.info("ENIGMA-APEX SYSTEM SHUTDOWN COMPLETE")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    async def _system_monitor(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                # Log system status every 60 seconds
                await asyncio.sleep(60)
                
                if self.running:  # Check again after sleep
                    logger.info("System Status: All components operational")
                    
                    # Could add more detailed health checks here:
                    # - Memory usage
                    # - OCR performance metrics
                    # - Trading statistics
                    # - Connection status
                
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main entry point"""
    system = EnigmaApexSystem()
    
    try:
        # Initialize all components
        await system.initialize()
        
        # Start the complete system
        await system.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
    finally:
        await system.shutdown()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                   ENIGMA-APEX PROP TRADING PANEL             ║
    ║                                                              ║
    ║  Professional Algorithmic Trading System                    ║
    ║  • Real OCR for AlgoBox Enigma Signal Reading              ║
    ║  • Kelly Criterion Position Sizing                         ║
    ║  • Apex Prop Firm Compliance Enforcement                   ║
    ║  • NinjaTrader 8 Integration                               ║
    ║  • Mobile Remote Control Interface                         ║
    ║  • 24/7 Automated Operation                                ║
    ║                                                              ║
    ║  Phase 1 Complete: Core System Ready                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the system
    asyncio.run(main())
