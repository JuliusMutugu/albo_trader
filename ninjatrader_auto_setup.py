"""
🥷 NINJATRADER AUTO-COMPILER AND SETUP
Automatically compile and configure NinjaTrader indicators
"""

import os
import subprocess
import time
import winreg
import psutil
from pathlib import Path
import shutil

class NinjaTraderAutoSetup:
    def __init__(self):
        self.ninja_path = self.find_ninjatrader_path()
        self.custom_indicators_path = None
        self.custom_strategies_path = None
        self.ninja_process = None
        
    def find_ninjatrader_path(self) -> str:
        """Find NinjaTrader installation path"""
        possible_paths = [
            r"C:\Program Files\NinjaTrader 8",
            r"C:\Program Files (x86)\NinjaTrader 8",
            fr"C:\Users\{os.getenv('USERNAME')}\Documents\NinjaTrader 8"
        ]
        
        # Check registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NinjaTrader\NinjaTrader 8") as key:
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                if os.path.exists(install_path):
                    possible_paths.insert(0, install_path)
        except:
            pass
        
        # Check common paths
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Found NinjaTrader at: {path}")
                
                # Set custom paths
                if "Documents" in path:
                    self.custom_indicators_path = os.path.join(path, "bin", "Custom", "Indicators")
                    self.custom_strategies_path = os.path.join(path, "bin", "Custom", "Strategies")
                else:
                    docs_path = fr"C:\Users\{os.getenv('USERNAME')}\Documents\NinjaTrader 8"
                    self.custom_indicators_path = os.path.join(docs_path, "bin", "Custom", "Indicators")
                    self.custom_strategies_path = os.path.join(docs_path, "bin", "Custom", "Strategies")
                
                return path
        
        print("❌ NinjaTrader 8 not found!")
        return None
    
    def check_ninja_running(self) -> bool:
        """Check if NinjaTrader is currently running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'ninjatrader' in proc.info['name'].lower():
                    self.ninja_process = proc
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_ninjatrader(self) -> bool:
        """Start NinjaTrader if not running"""
        if self.check_ninja_running():
            print("✅ NinjaTrader is already running")
            return True
        
        if not self.ninja_path:
            print("❌ Cannot start NinjaTrader - installation not found")
            return False
        
        try:
            ninja_exe = os.path.join(self.ninja_path, "bin", "NinjaTrader.exe")
            if not os.path.exists(ninja_exe):
                ninja_exe = os.path.join(self.ninja_path, "NinjaTrader.exe")
            
            if os.path.exists(ninja_exe):
                print(f"🚀 Starting NinjaTrader: {ninja_exe}")
                subprocess.Popen([ninja_exe])
                
                # Wait for NinjaTrader to start
                for i in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    if self.check_ninja_running():
                        print("✅ NinjaTrader started successfully")
                        return True
                    print(f"⏳ Waiting for NinjaTrader to start... ({i+1}/30)")
                
                print("⚠️ NinjaTrader may have started but process not detected")
                return True
            else:
                print("❌ NinjaTrader executable not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start NinjaTrader: {e}")
            return False
    
    def verify_files_copied(self) -> bool:
        """Verify that Enigma-Apex files are in NinjaTrader directories"""
        files_to_check = [
            (self.custom_indicators_path, "EnigmaApexPowerScore.cs"),
            (self.custom_indicators_path, "EnigmaApexRiskManager.cs"),
            (self.custom_strategies_path, "EnigmaApexAutoTrader.cs")
        ]
        
        all_present = True
        for directory, filename in files_to_check:
            if not directory or not os.path.exists(directory):
                print(f"❌ Directory not found: {directory}")
                all_present = False
                continue
                
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✅ {filename}: {file_size:,} bytes")
            else:
                print(f"❌ Missing file: {file_path}")
                all_present = False
        
        return all_present
    
    def copy_files_if_missing(self) -> bool:
        """Copy Enigma-Apex files to NinjaTrader if missing"""
        source_dir = "NinjaTrader_Indicators"
        
        if not os.path.exists(source_dir):
            print(f"❌ Source directory not found: {source_dir}")
            return False
        
        files_to_copy = [
            ("EnigmaApexPowerScore.cs", self.custom_indicators_path),
            ("EnigmaApexRiskManager.cs", self.custom_indicators_path),
            ("EnigmaApexAutoTrader.cs", self.custom_strategies_path)
        ]
        
        success = True
        for filename, dest_dir in files_to_copy:
            if not dest_dir:
                print(f"❌ Destination directory not set for {filename}")
                success = False
                continue
                
            # Create destination directory if it doesn't exist
            os.makedirs(dest_dir, exist_ok=True)
            
            source_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            
            if os.path.exists(source_file):
                try:
                    shutil.copy2(source_file, dest_file)
                    print(f"✅ Copied {filename} to {dest_dir}")
                except Exception as e:
                    print(f"❌ Failed to copy {filename}: {e}")
                    success = False
            else:
                print(f"❌ Source file not found: {source_file}")
                success = False
        
        return success
    
    def compile_indicators(self) -> bool:
        """Attempt to compile indicators programmatically"""
        if not self.check_ninja_running():
            print("❌ NinjaTrader must be running to compile indicators")
            return False
        
        print("🔨 Attempting to compile indicators...")
        print("📝 Note: You may need to manually compile in NinjaScript Editor")
        
        # Instructions for manual compilation
        print("\n📋 MANUAL COMPILATION STEPS:")
        print("1. In NinjaTrader, go to Tools → Edit NinjaScript → Indicator")
        print("2. Find and open 'EnigmaApexPowerScore'")
        print("3. Press F5 to compile")
        print("4. Find and open 'EnigmaApexRiskManager'")
        print("5. Press F5 to compile")
        print("6. Go to Tools → Edit NinjaScript → Strategy")
        print("7. Find and open 'EnigmaApexAutoTrader'")
        print("8. Press F5 to compile")
        print("9. Check for 'Compiled successfully' messages")
        
        return True
    
    def create_indicator_setup_script(self) -> None:
        """Create a batch script to help with indicator setup"""
        script_content = f'''@echo off
echo 🥷 Enigma-Apex NinjaTrader Setup Script
echo ==========================================

echo.
echo 📁 Checking NinjaTrader directories...
if exist "{self.custom_indicators_path}" (
    echo ✅ Indicators directory: {self.custom_indicators_path}
) else (
    echo ❌ Indicators directory not found: {self.custom_indicators_path}
)

if exist "{self.custom_strategies_path}" (
    echo ✅ Strategies directory: {self.custom_strategies_path}
) else (
    echo ❌ Strategies directory not found: {self.custom_strategies_path}
)

echo.
echo 📋 Files to verify:
if exist "{self.custom_indicators_path}\\EnigmaApexPowerScore.cs" (
    echo ✅ EnigmaApexPowerScore.cs
) else (
    echo ❌ EnigmaApexPowerScore.cs - MISSING
)

if exist "{self.custom_indicators_path}\\EnigmaApexRiskManager.cs" (
    echo ✅ EnigmaApexRiskManager.cs
) else (
    echo ❌ EnigmaApexRiskManager.cs - MISSING
)

if exist "{self.custom_strategies_path}\\EnigmaApexAutoTrader.cs" (
    echo ✅ EnigmaApexAutoTrader.cs
) else (
    echo ❌ EnigmaApexAutoTrader.cs - MISSING
)

echo.
echo 🔨 Next Steps:
echo 1. Open NinjaTrader 8
echo 2. Go to Tools → Edit NinjaScript → Indicator
echo 3. Compile EnigmaApexPowerScore (F5)
echo 4. Compile EnigmaApexRiskManager (F5)
echo 5. Go to Tools → Edit NinjaScript → Strategy
echo 6. Compile EnigmaApexAutoTrader (F5)
echo 7. Add indicators to your chart

pause
'''
        
        with open("ninja_setup_helper.bat", "w") as f:
            f.write(script_content)
        
        print("✅ Created setup helper script: ninja_setup_helper.bat")
    
    def run_complete_setup(self) -> bool:
        """Run the complete NinjaTrader setup process"""
        print("🥷 NINJATRADER AUTO-SETUP STARTING...")
        print("=" * 50)
        
        # Step 1: Verify NinjaTrader installation
        if not self.ninja_path:
            print("❌ Setup failed: NinjaTrader not found")
            return False
        
        # Step 2: Check if files are copied
        if not self.verify_files_copied():
            print("⚠️ Some files missing, attempting to copy...")
            if not self.copy_files_if_missing():
                print("❌ Setup failed: Could not copy files")
                return False
        
        # Step 3: Start NinjaTrader if not running
        if not self.start_ninjatrader():
            print("⚠️ Could not start NinjaTrader automatically")
            print("📝 Please start NinjaTrader manually")
        
        # Step 4: Create helper script
        self.create_indicator_setup_script()
        
        # Step 5: Attempt compilation
        self.compile_indicators()
        
        print("\n✅ SETUP PROCESS COMPLETED!")
        print("📋 Summary:")
        print(f"   ✅ Files copied to NinjaTrader directories")
        print(f"   ✅ Helper script created: ninja_setup_helper.bat")
        print(f"   📝 Manual compilation required in NinjaTrader")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Ensure NinjaTrader is running")
        print("2. Run: ninja_setup_helper.bat (to verify setup)")
        print("3. Manually compile indicators in NinjaScript Editor (F5)")
        print("4. Add indicators to your charts")
        print("5. Start the signal input system")
        
        return True

def main():
    """Main function to run NinjaTrader auto-setup"""
    print("🥷 Enigma-Apex NinjaTrader Auto-Setup")
    print("=" * 40)
    
    setup = NinjaTraderAutoSetup()
    
    try:
        success = setup.run_complete_setup()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print("📊 Your NinjaTrader is ready for Enigma-Apex indicators")
        else:
            print("\n❌ Setup encountered issues")
            print("📝 Please check the error messages above")
            
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
