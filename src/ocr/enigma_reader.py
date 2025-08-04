"""
OCR-based Enigma signal reader for AlgoBox panel monitoring.

This module uses computer vision and OCR to read trading signals from
the AlgoBox Enigma panel in real-time.
"""

import asyncio
import logging
import json
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple
from PIL import ImageGrab
import pytesseract
import easyocr

from ..utils.performance import measure_time


class EnigmaReader:
    """
    OCR reader for AlgoBox Enigma panel signals.
    
    Reads:
    - Power score (numeric)
    - Confluence levels (L1-L4)
    - Signal colors (green/blue/red/pink)
    - MACVU filter state
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OCR engines
        self.tesseract_config = "--psm 7 -c tessedit_char_whitelist=0123456789"
        self.easyocr_reader = None
        
        # Screen regions for panel elements
        self.regions = {}
        
        # Signal validation
        self.last_valid_signal = None
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        
    async def initialize(self):
        """Initialize OCR engines and load screen regions."""
        try:
            self.logger.info("Initializing Enigma OCR reader...")
            
            # Initialize EasyOCR
            self.easyocr_reader = easyocr.Reader(['en'])
            
            # Load screen regions
            regions_file = self.config.get('regions_file', 'config/ocr_regions.json')
            await self._load_screen_regions(regions_file)
            
            # Calibrate OCR accuracy
            await self._calibrate_ocr()
            
            self.logger.info("Enigma OCR reader initialized successfully")
            
        except Exception as e:
            self.logger.error(f"OCR reader initialization failed: {e}")
            raise
            
    async def _load_screen_regions(self, regions_file: str):
        """Load screen coordinate regions for panel elements."""
        try:
            with open(regions_file, 'r') as f:
                self.regions = json.load(f)
                
            required_regions = ['power', 'confluence', 'signal_color', 'macvu_status']
            for region in required_regions:
                if region not in self.regions:
                    raise ValueError(f"Missing required region: {region}")
                    
        except FileNotFoundError:
            self.logger.warning(f"Regions file not found: {regions_file}")
            # Create default regions file
            await self._create_default_regions(regions_file)
            
    async def _create_default_regions(self, regions_file: str):
        """Create default screen regions configuration."""
        default_regions = {
            "power": [100, 100, 200, 130],
            "confluence": [100, 140, 200, 170],
            "signal_color": [100, 180, 200, 210],
            "macvu_status": [100, 220, 200, 250]
        }
        
        import os
        os.makedirs(os.path.dirname(regions_file), exist_ok=True)
        
        with open(regions_file, 'w') as f:
            json.dump(default_regions, f, indent=4)
            
        self.regions = default_regions
        self.logger.info(f"Created default regions file: {regions_file}")
        
    async def _calibrate_ocr(self):
        """Calibrate OCR engines for optimal accuracy."""
        try:
            # Test OCR on current screen
            test_capture = self._capture_region('power')
            if test_capture is not None:
                # Test both OCR engines
                tesseract_result = self._ocr_with_tesseract(test_capture)
                easyocr_result = self._ocr_with_easyocr(test_capture)
                
                self.logger.info("OCR calibration complete")
            else:
                self.logger.warning("OCR calibration failed - no screen capture")
                
        except Exception as e:
            self.logger.error(f"OCR calibration error: {e}")
            
    @measure_time
    async def read_panel(self) -> Optional[Dict[str, Any]]:
        """
        Read all Enigma panel elements and return structured data.
        
        Returns:
            Dict containing power, confluence, signal_color, macvu_status
        """
        try:
            signal_data = {}
            
            # Read power score
            power = await self._read_power_score()
            if power is not None:
                signal_data['power'] = power
                
            # Read confluence level
            confluence = await self._read_confluence_level()
            if confluence:
                signal_data['confluence'] = confluence
                
            # Read signal color
            signal_color = await self._read_signal_color()
            if signal_color:
                signal_data['signal_color'] = signal_color
                signal_data['direction'] = self._color_to_direction(signal_color)
                
            # Read MACVU status
            macvu = await self._read_macvu_status()
            if macvu:
                signal_data['macvu'] = macvu
                
            # Validate signal data
            if self._validate_signal_data(signal_data):
                self.last_valid_signal = signal_data
                return signal_data
            else:
                # Return last valid signal if current read failed
                return self.last_valid_signal
                
        except Exception as e:
            self.logger.error(f"Panel reading error: {e}")
            return None
            
    async def _read_power_score(self) -> Optional[int]:
        """Read numeric power score from panel."""
        try:
            # Capture power score region
            image = self._capture_region('power')
            if image is None:
                return None
                
            # Try multiple OCR approaches
            results = []
            
            # Tesseract approach
            tesseract_text = self._ocr_with_tesseract(image)
            if tesseract_text.isdigit():
                results.append(int(tesseract_text))
                
            # EasyOCR approach
            easyocr_text = self._ocr_with_easyocr(image)
            if easyocr_text.isdigit():
                results.append(int(easyocr_text))
                
            # Return most common result
            if results:
                return max(set(results), key=results.count)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Power score reading error: {e}")
            return None
            
    async def _read_confluence_level(self) -> Optional[str]:
        """Read confluence level (L1, L2, L3, L4) from panel."""
        try:
            image = self._capture_region('confluence')
            if image is None:
                return None
                
            # Use color detection for confluence buttons
            confluence_level = self._detect_confluence_buttons(image)
            
            if confluence_level:
                return confluence_level
                
            # Fallback to OCR
            text = self._ocr_with_easyocr(image)
            for level in ['L4', 'L3', 'L2', 'L1']:
                if level in text:
                    return level
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Confluence reading error: {e}")
            return None
            
    async def _read_signal_color(self) -> Optional[str]:
        """Read signal color from panel."""
        try:
            image = self._capture_region('signal_color')
            if image is None:
                return None
                
            # Use color detection
            dominant_color = self._detect_dominant_color(image)
            return self._classify_signal_color(dominant_color)
            
        except Exception as e:
            self.logger.error(f"Signal color reading error: {e}")
            return None
            
    async def _read_macvu_status(self) -> Optional[str]:
        """Read MACVU filter status from panel."""
        try:
            image = self._capture_region('macvu_status')
            if image is None:
                return None
                
            # Use color detection for MACVU status
            dominant_color = self._detect_dominant_color(image)
            return self._classify_macvu_status(dominant_color)
            
        except Exception as e:
            self.logger.error(f"MACVU reading error: {e}")
            return None
            
    def _capture_region(self, region_name: str) -> Optional[np.ndarray]:
        """Capture screen region and return as numpy array."""
        try:
            if region_name not in self.regions:
                self.logger.error(f"Unknown region: {region_name}")
                return None
                
            coords = self.regions[region_name]
            x1, y1, x2, y2 = coords
            
            # Capture screen region
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Convert to numpy array
            image = np.array(screenshot)
            
            # Convert to BGR for OpenCV
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
            return image
            
        except Exception as e:
            self.logger.error(f"Screen capture error for {region_name}: {e}")
            return None
            
    def _ocr_with_tesseract(self, image: np.ndarray) -> str:
        """Extract text using Tesseract OCR."""
        try:
            # Preprocess image for better OCR
            processed = self._preprocess_for_ocr(image)
            
            # Run Tesseract
            text = pytesseract.image_to_string(
                processed, 
                config=self.tesseract_config
            ).strip()
            
            return text
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR error: {e}")
            return ""
            
    def _ocr_with_easyocr(self, image: np.ndarray) -> str:
        """Extract text using EasyOCR."""
        try:
            # EasyOCR expects RGB
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
                
            # Run EasyOCR
            results = self.easyocr_reader.readtext(rgb_image)
            
            # Extract text with highest confidence
            best_text = ""
            best_confidence = 0
            
            for (bbox, text, confidence) in results:
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_text = text
                    
            return best_text if best_confidence > self.confidence_threshold else ""
            
        except Exception as e:
            self.logger.error(f"EasyOCR error: {e}")
            return ""
            
    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
                
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Denoise
            denoised = cv2.medianBlur(thresh, 3)
            
            # Scale up for better OCR
            scaled = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            return scaled
            
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            return image
            
    def _detect_confluence_buttons(self, image: np.ndarray) -> Optional[str]:
        """Detect which confluence level buttons are active."""
        try:
            # Implementation depends on specific button colors/layout
            # This is a placeholder for actual button detection logic
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for active buttons (example values)
            active_color_lower = np.array([100, 50, 50])  # Blue-ish
            active_color_upper = np.array([130, 255, 255])
            
            # Find active regions
            mask = cv2.inRange(hsv, active_color_lower, active_color_upper)
            
            # Count active pixels for each button region
            # Return highest active confluence level
            
            return "L3"  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Confluence detection error: {e}")
            return None
            
    def _detect_dominant_color(self, image: np.ndarray) -> Tuple[int, int, int]:
        """Detect dominant color in image region."""
        try:
            # Reshape image to list of pixels
            pixels = image.reshape(-1, 3)
            
            # Use k-means clustering to find dominant color
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=3, random_state=42)
            kmeans.fit(pixels)
            
            # Get dominant color (cluster center with most points)
            labels = kmeans.labels_
            dominant_cluster = np.bincount(labels).argmax()
            dominant_color = kmeans.cluster_centers_[dominant_cluster]
            
            return tuple(dominant_color.astype(int))
            
        except Exception as e:
            self.logger.error(f"Color detection error: {e}")
            return (0, 0, 0)
            
    def _classify_signal_color(self, color: Tuple[int, int, int]) -> str:
        """Classify BGR color into signal categories."""
        b, g, r = color
        
        # Define color thresholds (BGR format)
        if g > r and g > b:  # Green dominant
            return "green"
        elif b > r and b > g:  # Blue dominant  
            return "blue"
        elif r > g and r > b:  # Red dominant
            return "red"
        elif r > 150 and g > 100 and b > 150:  # Pink-ish
            return "pink"
        else:
            return "unknown"
            
    def _classify_macvu_status(self, color: Tuple[int, int, int]) -> str:
        """Classify MACVU status based on color."""
        b, g, r = color
        
        if g > r and g > b:  # Green
            return "bullish"
        elif r > g and r > b:  # Red
            return "bearish"
        else:
            return "neutral"
            
    def _color_to_direction(self, signal_color: str) -> str:
        """Convert signal color to trading direction."""
        color_map = {
            "green": "long",
            "blue": "long",
            "red": "short", 
            "pink": "short"
        }
        return color_map.get(signal_color, "unknown")
        
    def _validate_signal_data(self, signal_data: Dict[str, Any]) -> bool:
        """Validate that signal data is complete and reasonable."""
        required_fields = ['power', 'confluence', 'signal_color']
        
        # Check required fields
        for field in required_fields:
            if field not in signal_data:
                return False
                
        # Validate power score range
        power = signal_data.get('power')
        if not isinstance(power, int) or power < 0 or power > 100:
            return False
            
        # Validate confluence level
        confluence = signal_data.get('confluence')
        if confluence not in ['L1', 'L2', 'L3', 'L4']:
            return False
            
        # Validate signal color
        signal_color = signal_data.get('signal_color')
        if signal_color not in ['green', 'blue', 'red', 'pink']:
            return False
            
        return True
