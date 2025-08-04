"""
OCR Processor - Real-time AlgoBox Enigma Panel Reading
Multi-engine OCR system with validation and confidence scoring
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

try:
    import cv2
    import easyocr
    import pytesseract
    import mss
    from PIL import Image, ImageGrab
    
    # Configure Tesseract path for Windows
    import os
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        # Try alternative paths
        alt_paths = [
            r'C:\Users\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        for path in alt_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
        else:
            logging.warning("Tesseract executable not found in standard locations")
            
except ImportError as e:
    logging.error(f"Required OCR libraries not installed: {e}")
    raise

@dataclass
class OCRResult:
    """OCR processing result with confidence scoring"""
    text: str
    confidence: float
    region_name: str
    timestamp: datetime
    processing_time_ms: int
    validated: bool

@dataclass
class EnigmaData:
    """Processed Enigma panel data"""
    power_score: int
    confluence_level: str
    signal_color: str
    macvu_state: str
    atr_value: float
    current_price: float
    timestamp: datetime
    confidence: float
    valid: bool

class OCRProcessor:
    """
    Multi-engine OCR processor for reading AlgoBox Enigma panel
    """
    
    def __init__(self, regions_config: str = "config/ocr_regions.json", confidence_threshold: float = 0.8):
        self.regions_config_path = Path(regions_config)
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # OCR engines
        self.easy_reader = None
        self.tesseract_config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        
        # Screen capture
        self.sct = None
        
        # Region definitions
        self.regions = {}
        self.screen_resolution = None
        
        # Processing state
        self.running = False
        self.last_reading = None
        self.processing_stats = {
            'total_readings': 0,
            'successful_readings': 0,
            'average_confidence': 0.0,
            'last_update': None
        }
        
        # Validation patterns
        self.validation_patterns = {
            'power_score': r'^\d{1,3}$',
            'confluence_level': r'^L[1-4]$',
            'signal_color': r'^(GREEN|BLUE|RED|PINK|NEUTRAL)$',
            'macvu_state': r'^(BULLISH|BEARISH|NEUTRAL)$',
            'price': r'^\d+\.?\d*$'
        }
    
    async def initialize(self):
        """Initialize OCR engines and load configuration"""
        try:
            self.logger.info("Initializing OCR Processor...")
            
            # Initialize EasyOCR
            self.easy_reader = easyocr.Reader(['en'], gpu=False)
            
            # Initialize screen capture
            self.sct = mss.mss()
            
            # Load region configurations
            await self._load_regions_config()
            
            # Auto-detect screen resolution
            self._detect_screen_resolution()
            
            self.logger.info("OCR Processor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OCR Processor: {e}")
            raise
    
    async def _load_regions_config(self):
        """Load OCR region configurations"""
        try:
            if self.regions_config_path.exists():
                with open(self.regions_config_path, 'r') as f:
                    config = json.load(f)
                    
                    # Check for new format with 'regions' key
                    if 'regions' in config:
                        self.regions = config.get('regions', {})
                        self.screen_resolution = config.get('screen_resolution', None)
                    else:
                        # Handle legacy format - convert to new format
                        self.logger.info("Converting legacy OCR regions format")
                        self.regions = self._convert_legacy_regions(config)
                        await self._save_regions_config()  # Save in new format
            else:
                # Create default configuration
                self.logger.info("Creating default OCR regions configuration")
                self.regions = self._get_default_regions()
                await self._save_regions_config()
                
        except Exception as e:
            self.logger.error(f"Error loading regions config: {e}")
            self.logger.info("Using default regions")
            self.regions = self._get_default_regions()
    
    def _convert_legacy_regions(self, legacy_config: Dict) -> Dict:
        """Convert legacy region format to new format"""
        converted = {}
        
        # Map legacy names to new names
        name_mapping = {
            'power': 'power_score',
            'confluence': 'confluence_level', 
            'signal_color': 'signal_color',
            'macvu_status': 'macvu_state'
        }
        
        for old_name, coordinates in legacy_config.items():
            if isinstance(coordinates, list) and len(coordinates) == 4:
                new_name = name_mapping.get(old_name, old_name)
                converted[new_name] = {
                    'coordinates': coordinates,
                    'description': f'{new_name.replace("_", " ").title()} region',
                    'validation_pattern': r'.*'  # Default pattern
                }
        
        return converted
    
    async def _save_regions_config(self):
        """Save current region configuration"""
        try:
            self.regions_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'regions': self.regions,
                'screen_resolution': self.screen_resolution,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.regions_config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving regions config: {e}")
    
    def _get_default_regions(self) -> Dict[str, Dict]:
        """Get default region definitions for common screen resolutions"""
        return {
            'power_score': {
                'coordinates': [100, 100, 200, 150],
                'description': 'Enigma Power Score display area',
                'validation_pattern': r'^\d{1,3}$'
            },
            'confluence_level': {
                'coordinates': [250, 100, 300, 150],
                'description': 'Confluence level indicator (L1-L4)',
                'validation_pattern': r'^L[1-4]$'
            },
            'signal_color': {
                'coordinates': [350, 100, 450, 150],
                'description': 'Signal color indicator',
                'validation_pattern': r'^(GREEN|BLUE|RED|PINK|NEUTRAL)$'
            },
            'macvu_state': {
                'coordinates': [500, 100, 600, 150],
                'description': 'MACVU filter state',
                'validation_pattern': r'^(BULLISH|BEARISH|NEUTRAL)$'
            },
            'current_price': {
                'coordinates': [100, 200, 250, 250],
                'description': 'Current market price',
                'validation_pattern': r'^\d+\.?\d*$'
            }
        }
    
    def _detect_screen_resolution(self):
        """Auto-detect current screen resolution"""
        try:
            monitor = self.sct.monitors[1]  # Primary monitor
            self.screen_resolution = f"{monitor['width']}x{monitor['height']}"
            self.logger.info(f"Detected screen resolution: {self.screen_resolution}")
        except Exception as e:
            self.logger.warning(f"Could not detect screen resolution: {e}")
            self.screen_resolution = "1920x1080"
    
    async def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """Get the latest OCR reading"""
        try:
            # Capture all regions
            captures = await self._capture_all_regions()
            if not captures:
                return None
            
            # Process each region with multi-engine OCR
            results = {}
            total_confidence = 0.0
            valid_readings = 0
            
            for region_name, image_data in captures.items():
                ocr_result = await self._process_region(region_name, image_data)
                if ocr_result and ocr_result.validated:
                    results[region_name] = ocr_result
                    total_confidence += ocr_result.confidence
                    valid_readings += 1
            
            # Calculate overall confidence
            overall_confidence = total_confidence / valid_readings if valid_readings > 0 else 0.0
            
            # Create EnigmaData if we have sufficient valid readings
            if valid_readings >= 3:  # Require at least 3 valid regions
                enigma_data = self._create_enigma_data(results, overall_confidence)
                self.last_reading = enigma_data.__dict__
                
                # Update statistics
                self.processing_stats['total_readings'] += 1
                self.processing_stats['successful_readings'] += 1
                self.processing_stats['average_confidence'] = (
                    (self.processing_stats['average_confidence'] * (self.processing_stats['successful_readings'] - 1) + 
                     overall_confidence) / self.processing_stats['successful_readings']
                )
                self.processing_stats['last_update'] = datetime.now()
                
                return enigma_data.__dict__
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in get_latest_reading: {e}")
            return None
    
    async def _capture_all_regions(self) -> Dict[str, np.ndarray]:
        """Capture all defined regions from screen"""
        captures = {}
        
        try:
            for region_name, region_config in self.regions.items():
                coordinates = region_config.get('coordinates', [0, 0, 100, 100])
                
                # Capture region
                bbox = {
                    'left': coordinates[0],
                    'top': coordinates[1], 
                    'width': coordinates[2] - coordinates[0],
                    'height': coordinates[3] - coordinates[1]
                }
                
                screenshot = self.sct.grab(bbox)
                img_array = np.array(screenshot)
                
                # Convert BGRA to RGB
                if img_array.shape[2] == 4:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
                
                captures[region_name] = img_array
                
        except Exception as e:
            self.logger.error(f"Error capturing regions: {e}")
            
        return captures
    
    async def _process_region(self, region_name: str, image: np.ndarray) -> Optional[OCRResult]:
        """Process a single region with multi-engine OCR"""
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image, region_name)
            
            # Try multiple OCR engines
            results = []
            
            # EasyOCR
            if self.easy_reader:
                try:
                    easy_results = self.easy_reader.readtext(processed_image, detail=1)
                    if easy_results:
                        text = ' '.join([result[1] for result in easy_results])
                        confidence = np.mean([result[2] for result in easy_results])
                        results.append(('easyocr', text.strip(), confidence))
                except Exception as e:
                    self.logger.debug(f"EasyOCR failed for {region_name}: {e}")
            
            # Tesseract
            try:
                # Convert to PIL Image for Tesseract
                pil_image = Image.fromarray(processed_image)
                tesseract_text = pytesseract.image_to_string(pil_image, config=self.tesseract_config).strip()
                # Tesseract doesn't provide confidence easily, use 0.8 as default
                results.append(('tesseract', tesseract_text, 0.8))
            except Exception as e:
                self.logger.debug(f"Tesseract failed for {region_name}: {e}")
            
            # Find consensus result
            consensus_result = self._find_consensus(results, region_name)
            
            if consensus_result:
                text, confidence = consensus_result
                processing_time = int((time.time() - start_time) * 1000)
                
                # Validate result
                validated = self._validate_ocr_result(region_name, text)
                
                return OCRResult(
                    text=text,
                    confidence=confidence,
                    region_name=region_name,
                    timestamp=datetime.now(),
                    processing_time_ms=processing_time,
                    validated=validated
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing region {region_name}: {e}")
            return None
    
    def _preprocess_image(self, image: np.ndarray, region_name: str) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Apply different preprocessing based on region type
            if region_name in ['power_score', 'current_price']:
                # For numeric regions: threshold for high contrast
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed = thresh
            else:
                # For text regions: noise reduction and enhancement
                denoised = cv2.medianBlur(gray, 3)
                processed = cv2.equalizeHist(denoised)
            
            # Resize for better OCR (if image is too small)
            height, width = processed.shape
            if height < 50 or width < 100:
                scale_factor = max(2, 50 // height)
                new_width = width * scale_factor
                new_height = height * scale_factor
                processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image for {region_name}: {e}")
            return image
    
    def _find_consensus(self, results: List[Tuple[str, str, float]], region_name: str) -> Optional[Tuple[str, float]]:
        """Find consensus result from multiple OCR engines"""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0][1], results[0][2]
        
        # Simple consensus: if two engines agree, use that result
        # Otherwise, use the result with highest confidence
        text_counts = {}
        for engine, text, confidence in results:
            if text in text_counts:
                text_counts[text]['count'] += 1
                text_counts[text]['total_confidence'] += confidence
            else:
                text_counts[text] = {'count': 1, 'total_confidence': confidence}
        
        # Find most common result
        best_text = None
        best_confidence = 0
        
        for text, data in text_counts.items():
            avg_confidence = data['total_confidence'] / data['count']
            score = data['count'] * avg_confidence  # Weight by agreement and confidence
            
            if score > best_confidence:
                best_confidence = avg_confidence
                best_text = text
        
        return (best_text, best_confidence) if best_text else None
    
    def _validate_ocr_result(self, region_name: str, text: str) -> bool:
        """Validate OCR result against expected patterns"""
        try:
            region_config = self.regions.get(region_name, {})
            pattern = region_config.get('validation_pattern', '.*')
            
            import re
            return bool(re.match(pattern, text))
            
        except Exception as e:
            self.logger.error(f"Error validating OCR result for {region_name}: {e}")
            return False
    
    def _create_enigma_data(self, results: Dict[str, OCRResult], confidence: float) -> EnigmaData:
        """Create EnigmaData from OCR results"""
        try:
            # Extract values with defaults
            power_score = int(results.get('power_score', OCRResult('0', 0, '', datetime.now(), 0, False)).text) if 'power_score' in results else 0
            confluence_level = results.get('confluence_level', OCRResult('L1', 0, '', datetime.now(), 0, False)).text
            signal_color = results.get('signal_color', OCRResult('NEUTRAL', 0, '', datetime.now(), 0, False)).text
            macvu_state = results.get('macvu_state', OCRResult('NEUTRAL', 0, '', datetime.now(), 0, False)).text
            
            # Parse price
            try:
                current_price = float(results.get('current_price', OCRResult('0', 0, '', datetime.now(), 0, False)).text) if 'current_price' in results else 0.0
            except ValueError:
                current_price = 0.0
            
            # Calculate ATR (simplified - in real implementation, this would come from NinjaTrader)
            atr_value = 10.0  # Default ATR value
            
            return EnigmaData(
                power_score=power_score,
                confluence_level=confluence_level,
                signal_color=signal_color,
                macvu_state=macvu_state,
                atr_value=atr_value,
                current_price=current_price,
                timestamp=datetime.now(),
                confidence=confidence,
                valid=confidence >= self.confidence_threshold
            )
            
        except Exception as e:
            self.logger.error(f"Error creating EnigmaData: {e}")
            return EnigmaData(0, 'L1', 'NEUTRAL', 'NEUTRAL', 10.0, 0.0, datetime.now(), 0.0, False)
    
    async def calibrate_regions(self, reference_image_path: str = None):
        """Auto-calibrate region positions"""
        # This would implement template matching to auto-detect regions
        # For now, provide manual calibration interface
        self.logger.info("Region calibration would be implemented here")
        pass
    
    async def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.sct:
            self.sct.close()
    
    def is_healthy(self) -> bool:
        """Check if OCR processor is healthy"""
        return (
            self.easy_reader is not None and
            self.sct is not None and
            len(self.regions) > 0
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get OCR processing statistics"""
        return self.processing_stats.copy()
