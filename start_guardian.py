"""
Enigma-Apex Prop Trading Panel
Core Guardian Engine - Main Entry Point

This is the main application entry point that orchestrates all components
of the Guardian trading system.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from src.core.config_manager import ConfigManager
from src.core.guardian_engine import GuardianEngine

# Direct component imports
from src.ocr.ocr_processor import OCRProcessor
from src.kelly.kelly_engine import KellyEngine
from src.cadence.cadence_tracker import CadenceTracker
from src.compliance.compliance_monitor import ComplianceMonitor
from src.websocket.websocket_server import WebSocketServer
from src.database.database_manager import DatabaseManager
from src.utils.logger import setup_logger

class GuardianApplication:
    """Main application class that coordinates all Guardian components"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.running = False
        
        # Core components
        self.ocr_processor = None
        self.kelly_engine = None
        self.cadence_tracker = None
        self.compliance_engine = None
        self.guardian_engine = None
        self.websocket_server = None
        self.mobile_controller = None
        
        # Setup logging
        self.logger = setup_logger(
            name=__name__,
            log_level=self.config_manager.get('logging.level', 'INFO')
        )
        
    async def initialize(self):
        """Initialize all Guardian components"""
        try:
            self.logger.info("Initializing Guardian Application...")
            
            # Load configuration
            config = self.config_manager.get_all_config()
            
            # Initialize core Guardian engine (handles all component initialization)
            self.guardian_engine = GuardianEngine(config)
            await self.guardian_engine.initialize()
            
            # Initialize WebSocket server
            websocket_config = config.get('websocket', {})
            self.websocket_server = WebSocketServer(
                host=websocket_config.get('host', 'localhost'),
                port=websocket_config.get('port', 8765)
            )
            
            # WebSocket server handles mobile communication
            self.logger.info("Guardian Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Guardian Application: {e}")
            raise
    
    async def start(self):
        """Start the Guardian application"""
        try:
            self.logger.info("Starting Guardian Application...")
            self.running = True
            
            # Start all components
            tasks = [
                self.guardian_engine.start(),
                self.websocket_server.start(),
                self.mobile_controller.start(),
                self._monitor_system_health()
            ]
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"Error starting Guardian Application: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the Guardian application gracefully"""
        self.logger.info("Stopping Guardian Application...")
        self.running = False
        
        # Stop all components
        if self.guardian_engine:
            await self.guardian_engine.stop()
        
        if self.websocket_server:
            await self.websocket_server.stop()
        
        if self.mobile_controller:
            await self.mobile_controller.stop()
        
        if self.ocr_processor:
            await self.ocr_processor.cleanup()
        
        self.logger.info("Guardian Application stopped")
    
    async def _monitor_system_health(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                # Check component health
                health_status = {
                    'ocr_processor': self.ocr_processor.is_healthy() if self.ocr_processor else False,
                    'kelly_engine': self.kelly_engine.is_healthy() if self.kelly_engine else False,
                    'cadence_tracker': self.cadence_tracker.is_healthy() if self.cadence_tracker else False,
                    'compliance_engine': self.compliance_engine.is_healthy() if self.compliance_engine else False,
                    'websocket_server': self.websocket_server.is_running() if self.websocket_server else False
                }
                
                # Log health status
                unhealthy_components = [comp for comp, healthy in health_status.items() if not healthy]
                if unhealthy_components:
                    self.logger.warning(f"Unhealthy components: {unhealthy_components}")
                else:
                    self.logger.debug("All components healthy")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main application entry point"""
    app = GuardianApplication()
    
    try:
        # Setup signal handlers
        app.setup_signal_handlers()
        
        # Initialize and start the application
        await app.initialize()
        await app.start()
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    finally:
        await app.stop()
    
    return 0

if __name__ == "__main__":
    # Ensure we're running in the correct directory
    import os
    os.chdir(Path(__file__).parent)
    
    # Run the application
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
