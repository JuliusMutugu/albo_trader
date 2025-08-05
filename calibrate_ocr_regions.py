"""
🎯 AlgoBox Enigma OCR Calibration Tool
Quick setup for screen coordinate capture
"""

import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import pyautogui
from PIL import Image, ImageTk

class OCRCalibrator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AlgoBox Enigma OCR Calibrator")
        self.root.geometry("600x400")
        
        self.regions = {}
        self.setup_ui()
        
    def setup_ui(self):
        title = tk.Label(self.root, text="AlgoBox Enigma OCR Calibrator", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        instructions = tk.Label(self.root, 
                               text="1. Position AlgoBox Enigma panel visibly on screen\n"
                                    "2. Click 'Capture Region' for each element\n"
                                    "3. Click and drag to select screen area\n"
                                    "4. Save configuration when complete",
                               justify=tk.LEFT)
        instructions.pack(pady=10)
        
        # Region capture buttons
        regions_to_capture = [
            ("Power Score", "power_score"),
            ("L1 Confluence", "confluence_l1"), 
            ("L2 Confluence", "confluence_l2"),
            ("L3 Confluence", "confluence_l3"),
            ("L4 Confluence", "confluence_l4"),
            ("Signal Color", "signal_color"),
            ("MACVU Status", "macvu_status"),
            ("ATR Value", "atr_value")
        ]
        
        for display_name, region_key in regions_to_capture:
            btn = tk.Button(self.root, text=f"Capture {display_name}",
                           command=lambda key=region_key, name=display_name: self.capture_region(key, name))
            btn.pack(pady=5)
            
        # Save button
        save_btn = tk.Button(self.root, text="Save Configuration", 
                           command=self.save_config, bg="green", fg="white",
                           font=("Arial", 12, "bold"))
        save_btn.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Ready to capture regions", 
                                    fg="blue")
        self.status_label.pack(pady=5)
        
    def capture_region(self, region_key, display_name):
        """Capture screen region with click and drag"""
        self.root.withdraw()  # Hide main window
        
        messagebox.showinfo("Capture Region", 
                           f"Position your mouse at TOP-LEFT of {display_name} area, then click OK")
        
        # Get first point
        print(f"Click at TOP-LEFT of {display_name} area...")
        x1, y1 = pyautogui.position()
        
        messagebox.showinfo("Capture Region", 
                           f"Now position mouse at BOTTOM-RIGHT of {display_name} area, then click OK")
        
        # Get second point  
        print(f"Click at BOTTOM-RIGHT of {display_name} area...")
        x2, y2 = pyautogui.position()
        
        # Store region
        self.regions[region_key] = {
            "x": min(x1, x2),
            "y": min(y1, y2), 
            "width": abs(x2 - x1),
            "height": abs(y2 - y1),
            "description": f"{display_name} capture area"
        }
        
        self.status_label.config(text=f"✅ Captured {display_name}: ({min(x1,x2)}, {min(y1,y2)}) {abs(x2-x1)}x{abs(y2-y1)}")
        self.root.deiconify()  # Show main window again
        
    def save_config(self):
        """Save captured regions to config file"""
        if len(self.regions) == 0:
            messagebox.showwarning("No Regions", "Please capture at least one region first")
            return
            
        config = {
            "screen_regions": self.regions,
            "calibration": {
                "screenshot_delay": 0.1,
                "ocr_confidence_threshold": 0.7,
                "color_tolerance": 10,
                "expected_colors": {
                    "green_signal": [0, 255, 0],
                    "red_signal": [255, 0, 0], 
                    "yellow_signal": [255, 255, 0],
                    "blue_signal": [0, 0, 255]
                }
            },
            "setup_complete": True,
            "calibration_timestamp": str(datetime.now())
        }
        
        try:
            import os
            os.makedirs("config", exist_ok=True)
            
            with open("config/ocr_regions.json", "w") as f:
                json.dump(config, f, indent=2)
                
            messagebox.showinfo("Success", 
                               f"Configuration saved successfully!\n"
                               f"Captured {len(self.regions)} regions\n"
                               f"File: config/ocr_regions.json")
            
            self.status_label.config(text=f"✅ Saved {len(self.regions)} regions to config/ocr_regions.json")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    from datetime import datetime
    
    print("🎯 AlgoBox Enigma OCR Calibrator")
    print("=" * 40)
    print("This tool will help you capture screen coordinates for OCR reading")
    print("Make sure AlgoBox Enigma panel is visible before starting")
    print()
    
    calibrator = OCRCalibrator()
    calibrator.run()
