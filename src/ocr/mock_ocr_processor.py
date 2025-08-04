"""
Mock OCR Processor - Placeholder when OCR libraries aren't available
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MockOCRResult:
    """Mock OCR result"""
    text: str = "mock_data"
    confidence: float = 0.0
    region_name: str = "mock"
    timestamp: datetime = None
    processing_time_ms: int = 0
    validated: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class MockEnigmaData:
    """Mock Enigma data"""
    power_score: int = 0
    confluence_level: str = "L1"
    signal_color: str = "NEUTRAL"
    macvu_state: str = "NEUTRAL"
    atr_value: float = 10.0
    current_price: float = 0.0
    timestamp: datetime = None
    confidence: float = 0.0
    valid: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MockOCRProcessor:
    """
    Mock OCR processor for when real OCR libraries aren't available
    """
    
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.warning("Using Mock OCR Processor - install OCR dependencies for real functionality")
        
        self.mock_power_score = 50
        self.processing_stats = {
            'total_readings': 0,
            'successful_readings': 0,
            'average_confidence': 0.0,
            'last_update': None
        }
    
    async def initialize(self):
        """Mock initialization"""
        self.logger.info("Mock OCR Processor initialized")
    
    async def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """Return mock OCR reading"""
        self.processing_stats['total_readings'] += 1
        
        # Simulate varying power scores
        self.mock_power_score = (self.mock_power_score + 1) % 100 + 20
        
        mock_data = MockEnigmaData(
            power_score=self.mock_power_score,
            confluence_level="L3",
            signal_color="GREEN" if self.mock_power_score > 60 else "NEUTRAL",
            macvu_state="BULLISH" if self.mock_power_score > 70 else "NEUTRAL",
            valid=True,
            confidence=0.5
        )
        
        self.processing_stats['successful_readings'] += 1
        self.processing_stats['last_update'] = datetime.now()
        
        return mock_data.__dict__
    
    async def cleanup(self):
        """Mock cleanup"""
        self.logger.info("Mock OCR Processor cleaned up")
    
    def is_healthy(self) -> bool:
        """Mock health check"""
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return mock statistics"""
        return self.processing_stats.copy()
