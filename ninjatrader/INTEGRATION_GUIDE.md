# 🥷 NinjaTrader 8 Integration Guide for Enigma-Apex

## 📋 **Prerequisites**

### Required Software:
1. **NinjaTrader 8** (latest version)
2. **Visual Studio 2019/2022** (Community edition is fine)
3. **Your Enigma-Apex WebSocket Server** (running on port 8765)

## 🚀 **Step-by-Step Integration Process**

### **Phase 1: Prepare Your Development Environment**

#### 1. Install NinjaTrader 8 Development Components
```
- Download NinjaTrader 8 from ninjatrader.com
- During installation, select "Include development components"
- This installs the NinjaScript Editor and development tools
```

#### 2. Verify WebSocket Server is Running
```powershell
# In your Enigma-Apex directory
cd c:\Users\Julimore\Downloads\albo
python src/websocket/websocket_server.py
```

#### 3. Test WebSocket Connectivity
```powershell
# Run your test to confirm server is working
python websocket_test.py
```

### **Phase 2: Create the NinjaScript AddOn**

#### 1. Open NinjaTrader 8
- Launch NinjaTrader 8
- Go to **Tools → NinjaScript Editor**

#### 2. Create New AddOn Project
- In NinjaScript Editor: **File → New → AddOn**
- Name it: `EnigmaApexDashboard`
- Click **Generate**

#### 3. Replace the Generated Code
- Copy the content from `EnigmaApexDashboard.cs` (created above)
- Replace all the default generated code
- **File → Save**

#### 4. Add Required References
Right-click on **References** in Solution Explorer and add:
- `System.Net.WebSockets`
- `System.Text.Json`

### **Phase 3: Compile and Test**

#### 1. Compile the AddOn
- In NinjaScript Editor: **Build → Compile**
- Check for any compilation errors
- Fix any missing references

#### 2. Enable the AddOn
- In NinjaTrader: **Tools → Options → NinjaScript**
- Find "EnigmaApexDashboard" in the AddOns list
- Check the **Enabled** checkbox
- Click **OK**

#### 3. Restart NinjaTrader
- Close NinjaTrader completely
- Restart it to load the new AddOn

### **Phase 4: Testing the Integration**

#### 1. Verify Dashboard Appears
- The Enigma-Apex dashboard should appear in the top-right corner
- Initial status should show "Connecting..."

#### 2. Check Connection Status
- Watch the **Output** window in NinjaTrader
- Look for connection messages
- Status should change to "Connected" with green text

#### 3. Test Real-Time Updates
Run this test script to simulate Enigma updates:

```python
# Create this as test_ninja_updates.py
import asyncio
import json
import websockets

async def send_enigma_update():
    async with websockets.connect('ws://localhost:8765') as websocket:
        # Send test update
        update = {
            "type": "enigma_update",
            "data": {
                "power_score": 75,
                "confluence_level": "L3",
                "signal_color": "GREEN",
                "macvu_state": "BULLISH"
            }
        }
        await websocket.send(json.dumps(update))
        print("Sent test update to dashboard")

asyncio.run(send_enigma_update())
```

## 🎯 **Testing Scenarios**

### **Test 1: Basic Connection**
1. Start WebSocket server
2. Start NinjaTrader
3. Verify dashboard shows "Connected"

### **Test 2: Real-Time Updates**
1. Run the update test script above
2. Watch dashboard values change in real-time
3. Signal color should change to GREEN

### **Test 3: Connection Recovery**
1. Stop WebSocket server
2. Dashboard should show "Disconnected"
3. Restart server
4. Dashboard should reconnect automatically

### **Test 4: Multiple Signals**
```python
# Advanced test - multiple signal types
import asyncio
import json
import websockets
import time

async def test_signal_sequence():
    async with websockets.connect('ws://localhost:8765') as websocket:
        
        # Test RED signal
        red_signal = {
            "type": "enigma_update", 
            "data": {
                "power_score": 25,
                "confluence_level": "L2",
                "signal_color": "RED",
                "macvu_state": "BEARISH"
            }
        }
        await websocket.send(json.dumps(red_signal))
        print("Sent RED signal")
        await asyncio.sleep(3)
        
        # Test YELLOW signal
        yellow_signal = {
            "type": "enigma_update",
            "data": {
                "power_score": 50,
                "confluence_level": "L1",
                "signal_color": "YELLOW", 
                "macvu_state": "NEUTRAL"
            }
        }
        await websocket.send(json.dumps(yellow_signal))
        print("Sent YELLOW signal")
        await asyncio.sleep(3)
        
        # Test GREEN signal
        green_signal = {
            "type": "enigma_update",
            "data": {
                "power_score": 90,
                "confluence_level": "L4",
                "signal_color": "GREEN",
                "macvu_state": "BULLISH"
            }
        }
        await websocket.send(json.dumps(green_signal))
        print("Sent GREEN signal")

asyncio.run(test_signal_sequence())
```

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **Dashboard Doesn't Appear**
- Check if AddOn is enabled in NinjaScript options
- Restart NinjaTrader after enabling
- Check Output window for error messages

#### **Connection Failed**
- Verify WebSocket server is running on port 8765
- Check Windows Firewall settings
- Test with the websocket_test.py script first

#### **Compilation Errors**
- Ensure all required references are added
- Check for typos in the code
- Verify NinjaTrader version compatibility

#### **Data Not Updating**
- Check WebSocket server logs for incoming connections
- Verify JSON message format
- Test with the update scripts provided

## 🎓 **Learning Objectives**

By completing this integration, you'll learn:

1. **WebSocket Communication** - Real-time bidirectional data flow
2. **NinjaScript Development** - Creating custom NinjaTrader tools
3. **JSON Message Protocols** - Structured data exchange
4. **Real-Time UI Updates** - Responsive trading interfaces
5. **Professional Trading Systems** - Industry-standard architectures

## 📈 **Next Steps for Advanced Learning**

1. **Add Trade Execution** - Connect signals to actual trades
2. **Risk Management** - Implement position sizing with Kelly Criterion
3. **Alert System** - Audio/visual alerts for signal changes
4. **Historical Data** - Log and analyze signal performance
5. **Multi-Timeframe** - Support multiple chart timeframes

## 🚨 **Important Notes**

- **Always test on demo accounts first**
- **This is for educational purposes**
- **Verify all signals before live trading**
- **Implement proper risk management**
- **Follow prop firm rules and guidelines**

---

**Ready to test? Start with Phase 1 and work through each step methodically. The system is designed to be educational while maintaining professional trading standards.** 🚀
