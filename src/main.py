"""
Main entry point for the Enigma-Apex Prop Trading Panel.

This module orchestrates the entire trading system, coordinating between
OCR signal reading, risk management, and NinjaTrader execution.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.core.guardian_engine import GuardianEngine
from src.utils.logger import setup_logger
from src.config.settings import load_settings


class EnigmaApexSystem:
    """Main system coordinator for the trading panel."""
    
    def __init__(self):
        self.guardian = None
        self.running = False
        self.logger = setup_logger(__name__)
        
    async def initialize(self):
        """Initialize all system components."""
        try:
            self.logger.info("Initializing Enigma-Apex Prop Trading Panel...")
            
            # Load configuration
            settings = load_settings()
            
            # Initialize guardian engine
            self.guardian = GuardianEngine(settings)
            await self.guardian.initialize()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.info("System initialization complete")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            raise
            
    async def start(self):
        """Start the trading system."""
        try:
            self.logger.info("Starting Enigma-Apex Trading System...")
            self.running = True
            
            # Start guardian engine
            await self.guardian.start()
            
            # Keep system running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"System error: {e}")
            raise
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown the system."""
        self.logger.info("Shutting down Enigma-Apex Trading System...")
        self.running = False
        
        if self.guardian:
            await self.guardian.shutdown()
            
        self.logger.info("System shutdown complete")
        
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False


async def main():
    """Main application entry point."""
    system = EnigmaApexSystem()
    
    try:
        await system.initialize()
        await system.start()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
