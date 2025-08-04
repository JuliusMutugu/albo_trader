/*
Enigma-Apex Guardian Dashboard for NinjaTrader 8
Professional trading dashboard with compliance monitoring and Kelly position sizing
*/

#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.DrawingTools;
using System.Net.WebSockets;
using System.Threading;
using Newtonsoft.Json;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
    public class EnigmaApexGuardian : Indicator
    {
        #region Variables
        private ClientWebSocket webSocket;
        private CancellationTokenSource cancellationTokenSource;
        private bool isConnected = false;
        
        // Guardian Data
        private double enigmaPowerScore = 0;
        private string enigmaConfluence = "L1";
        private string enigmaSignalColor = "NEUTRAL";
        private string macvuState = "NEUTRAL";
        private double kellyPercentage = 0;
        private double recommendedSize = 0;
        private bool complianceGreen = true;
        private string complianceMessage = "All systems normal";
        
        // Trading State
        private bool tradingEnabled = false;
        private bool emergencyStop = false;
        private double accountBalance = 50000;
        private double dailyPnL = 0;
        private double totalPnL = 0;
        
        // Dashboard Colors
        private Brush greenBrush = Brushes.LimeGreen;
        private Brush redBrush = Brushes.Red;
        private Brush yellowBrush = Brushes.Yellow;
        private Brush grayBrush = Brushes.Gray;
        private Brush blueBrush = Brushes.DodgerBlue;
        
        // Font
        private SimpleFont dashboardFont = new SimpleFont("Segoe UI", 12);
        private SimpleFont titleFont = new SimpleFont("Segoe UI", 16) { Bold = true };
        private SimpleFont statusFont = new SimpleFont("Segoe UI", 10);
        #endregion

        public override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Enigma-Apex Guardian Dashboard - Professional Prop Trading Panel";
                Name = "EnigmaApexGuardian";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                DisplayInDataBox = false;
                DrawOnPricePanel = true;
                DrawHorizontalGridLines = false;
                DrawVerticalGridLines = false;
                PaintPriceMarkers = false;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;
                IsSuspendedWhileInactive = false;
                
                // WebSocket Settings
                WebSocketUrl = "ws://localhost:8765/ninja";
                AutoConnect = true;
                ShowCompliancePanel = true;
                ShowKellyPanel = true;
                ShowEnigmaPanel = true;
                ShowControlPanel = true;
            }
            else if (State == State.Active)
            {
                // Initialize WebSocket connection
                if (AutoConnect)
                {
                    ConnectToGuardianSystem();
                }
            }
            else if (State == State.Terminated)
            {
                // Cleanup WebSocket
                DisconnectFromGuardianSystem();
            }
        }

        public override void OnBarUpdate()
        {
            // Update account information
            if (Account != null)
            {
                accountBalance = Account.Get(AccountItem.CashValue, Currency.UsDollar);
                dailyPnL = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);
            }
        }

        public override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (Bars == null || chartControl == null) return;

            // Dashboard position (top-right corner)
            int panelWidth = 300;
            int panelHeight = 400;
            int margin = 10;
            
            int startX = chartControl.CanvasRight - panelWidth - margin;
            int startY = margin;

            // Draw main dashboard background
            DrawDashboardBackground(chartControl, startX, startY, panelWidth, panelHeight);
            
            // Draw dashboard sections
            int currentY = startY + 10;
            
            // Title
            currentY = DrawTitle(chartControl, startX, currentY, panelWidth);
            
            // Connection Status
            currentY = DrawConnectionStatus(chartControl, startX, currentY, panelWidth);
            
            if (ShowEnigmaPanel)
            {
                currentY = DrawEnigmaPanel(chartControl, startX, currentY, panelWidth);
            }
            
            if (ShowKellyPanel)
            {
                currentY = DrawKellyPanel(chartControl, startX, currentY, panelWidth);
            }
            
            if (ShowCompliancePanel)
            {
                currentY = DrawCompliancePanel(chartControl, startX, currentY, panelWidth);
            }
            
            if (ShowControlPanel)
            {
                currentY = DrawControlPanel(chartControl, startX, currentY, panelWidth);
            }
        }

        #region Dashboard Drawing Methods
        
        private void DrawDashboardBackground(ChartControl chartControl, int x, int y, int width, int height)
        {
            // Semi-transparent background
            var backgroundBrush = new SolidColorBrush(Color.FromArgb(200, 30, 30, 30));
            var borderBrush = new SolidColorBrush(Colors.Gray);
            
            // Draw background rectangle
            SharpDX.RectangleF backgroundRect = new SharpDX.RectangleF(x, y, width, height);
            RenderTarget.FillRectangle(backgroundRect, backgroundBrush.ToDxBrush(RenderTarget));
            RenderTarget.DrawRectangle(backgroundRect, borderBrush.ToDxBrush(RenderTarget), 2);
        }
        
        private int DrawTitle(ChartControl chartControl, int x, int y, int width)
        {
            var titleBrush = new SolidColorBrush(Colors.White);
            var textFormat = titleFont.ToDirectWriteTextFormat();
            
            string title = "ENIGMA-APEX GUARDIAN";
            var textRect = new SharpDX.RectangleF(x + 10, y, width - 20, 30);
            
            RenderTarget.DrawText(title, textFormat, textRect, titleBrush.ToDxBrush(RenderTarget));
            
            return y + 35;
        }
        
        private int DrawConnectionStatus(ChartControl chartControl, int x, int y, int width)
        {
            var statusBrush = isConnected ? greenBrush : redBrush;
            var textBrush = new SolidColorBrush(Colors.White);
            var textFormat = statusFont.ToDirectWriteTextFormat();
            
            // Status indicator circle
            var statusRect = new SharpDX.RectangleF(x + 10, y, 10, 10);
            RenderTarget.FillEllipse(new SharpDX.Ellipse(new SharpDX.Vector2(x + 15, y + 5), 5, 5), 
                statusBrush.ToDxBrush(RenderTarget));
            
            // Status text
            string statusText = isConnected ? "CONNECTED" : "DISCONNECTED";
            var textRect = new SharpDX.RectangleF(x + 30, y - 2, width - 40, 15);
            RenderTarget.DrawText(statusText, textFormat, textRect, textBrush.ToDxBrush(RenderTarget));
            
            return y + 25;
        }
        
        private int DrawEnigmaPanel(ChartControl chartControl, int x, int y, int width)
        {
            var headerBrush = new SolidColorBrush(Colors.CornflowerBlue);
            var textBrush = new SolidColorBrush(Colors.White);
            var headerFormat = dashboardFont.ToDirectWriteTextFormat();
            var textFormat = statusFont.ToDirectWriteTextFormat();
            
            // Panel header
            var headerRect = new SharpDX.RectangleF(x + 5, y, width - 10, 20);
            RenderTarget.FillRectangle(headerRect, headerBrush.ToDxBrush(RenderTarget));
            
            string header = "ENIGMA SIGNALS";
            RenderTarget.DrawText(header, headerFormat, 
                new SharpDX.RectangleF(x + 10, y + 2, width - 20, 18), 
                new SolidColorBrush(Colors.White).ToDxBrush(RenderTarget));
            
            int currentY = y + 25;
            
            // Power Score
            DrawDataRow(chartControl, x, currentY, width, "Power Score:", 
                enigmaPowerScore.ToString("F0"), GetPowerScoreColor());
            currentY += 20;
            
            // Confluence
            DrawDataRow(chartControl, x, currentY, width, "Confluence:", 
                enigmaConfluence, GetConfluenceColor());
            currentY += 20;
            
            // Signal Color
            DrawDataRow(chartControl, x, currentY, width, "Signal:", 
                enigmaSignalColor, GetSignalColor());
            currentY += 20;
            
            // MACVU State
            DrawDataRow(chartControl, x, currentY, width, "MACVU:", 
                macvuState, GetMacvuColor());
            currentY += 20;
            
            return currentY + 10;
        }
        
        private int DrawKellyPanel(ChartControl chartControl, int x, int y, int width)
        {
            var headerBrush = new SolidColorBrush(Colors.DarkGreen);
            var headerFormat = dashboardFont.ToDirectWriteTextFormat();
            
            // Panel header
            var headerRect = new SharpDX.RectangleF(x + 5, y, width - 10, 20);
            RenderTarget.FillRectangle(headerRect, headerBrush.ToDxBrush(RenderTarget));
            
            string header = "KELLY POSITION SIZING";
            RenderTarget.DrawText(header, headerFormat, 
                new SharpDX.RectangleF(x + 10, y + 2, width - 20, 18), 
                new SolidColorBrush(Colors.White).ToDxBrush(RenderTarget));
            
            int currentY = y + 25;
            
            // Kelly Percentage
            DrawDataRow(chartControl, x, currentY, width, "Kelly %:", 
                (kellyPercentage * 100).ToString("F2") + "%", 
                kellyPercentage > 0.1 ? redBrush : kellyPercentage > 0.05 ? yellowBrush : greenBrush);
            currentY += 20;
            
            // Recommended Size
            DrawDataRow(chartControl, x, currentY, width, "Position Size:", 
                recommendedSize.ToString("F0") + " contracts", grayBrush);
            currentY += 20;
            
            return currentY + 10;
        }
        
        private int DrawCompliancePanel(ChartControl chartControl, int x, int y, int width)
        {
            var headerBrush = complianceGreen ? new SolidColorBrush(Colors.DarkGreen) : new SolidColorBrush(Colors.DarkRed);
            var headerFormat = dashboardFont.ToDirectWriteTextFormat();
            
            // Panel header
            var headerRect = new SharpDX.RectangleF(x + 5, y, width - 10, 20);
            RenderTarget.FillRectangle(headerRect, headerBrush.ToDxBrush(RenderTarget));
            
            string header = "APEX COMPLIANCE";
            RenderTarget.DrawText(header, headerFormat, 
                new SharpDX.RectangleF(x + 10, y + 2, width - 20, 18), 
                new SolidColorBrush(Colors.White).ToDxBrush(RenderTarget));
            
            int currentY = y + 25;
            
            // Account Balance
            DrawDataRow(chartControl, x, currentY, width, "Balance:", 
                "$" + accountBalance.ToString("F2"), grayBrush);
            currentY += 20;
            
            // Daily P&L
            DrawDataRow(chartControl, x, currentY, width, "Daily P&L:", 
                "$" + dailyPnL.ToString("F2"), dailyPnL >= 0 ? greenBrush : redBrush);
            currentY += 20;
            
            // Compliance Status
            DrawDataRow(chartControl, x, currentY, width, "Status:", 
                complianceMessage, complianceGreen ? greenBrush : redBrush);
            currentY += 20;
            
            return currentY + 10;
        }
        
        private int DrawControlPanel(ChartControl chartControl, int x, int y, int width)
        {
            var headerBrush = new SolidColorBrush(Colors.DarkSlateGray);
            var headerFormat = dashboardFont.ToDirectWriteTextFormat();
            
            // Panel header
            var headerRect = new SharpDX.RectangleF(x + 5, y, width - 10, 20);
            RenderTarget.FillRectangle(headerRect, headerBrush.ToDxBrush(RenderTarget));
            
            string header = "TRADING CONTROLS";
            RenderTarget.DrawText(header, headerFormat, 
                new SharpDX.RectangleF(x + 10, y + 2, width - 20, 18), 
                new SolidColorBrush(Colors.White).ToDxBrush(RenderTarget));
            
            int currentY = y + 25;
            
            // Trading Status
            string tradingStatus = emergencyStop ? "EMERGENCY STOP" : 
                                 tradingEnabled ? "TRADING ENABLED" : "TRADING DISABLED";
            Brush statusColor = emergencyStop ? redBrush : 
                              tradingEnabled ? greenBrush : yellowBrush;
            
            DrawDataRow(chartControl, x, currentY, width, "Status:", tradingStatus, statusColor);
            currentY += 30;
            
            return currentY;
        }
        
        private void DrawDataRow(ChartControl chartControl, int x, int y, int width, 
                               string label, string value, Brush valueBrush)
        {
            var labelBrush = new SolidColorBrush(Colors.LightGray);
            var textFormat = statusFont.ToDirectWriteTextFormat();
            
            // Label
            var labelRect = new SharpDX.RectangleF(x + 10, y, 100, 15);
            RenderTarget.DrawText(label, textFormat, labelRect, labelBrush.ToDxBrush(RenderTarget));
            
            // Value
            var valueRect = new SharpDX.RectangleF(x + 120, y, width - 130, 15);
            RenderTarget.DrawText(value, textFormat, valueRect, valueBrush.ToDxBrush(RenderTarget));
        }
        
        #endregion

        #region Color Helpers
        
        private Brush GetPowerScoreColor()
        {
            if (enigmaPowerScore >= 80) return greenBrush;
            if (enigmaPowerScore >= 50) return yellowBrush;
            return redBrush;
        }
        
        private Brush GetConfluenceColor()
        {
            switch (enigmaConfluence)
            {
                case "L4": return greenBrush;
                case "L3": return yellowBrush;
                case "L2": return yellowBrush;
                case "L1": return redBrush;
                default: return grayBrush;
            }
        }
        
        private Brush GetSignalColor()
        {
            switch (enigmaSignalColor.ToUpper())
            {
                case "GREEN": return greenBrush;
                case "BLUE": return blueBrush;
                case "RED": return redBrush;
                case "PINK": return new SolidColorBrush(Colors.Pink);
                default: return grayBrush;
            }
        }
        
        private Brush GetMacvuColor()
        {
            switch (macvuState.ToUpper())
            {
                case "BULLISH": return greenBrush;
                case "BEARISH": return redBrush;
                default: return grayBrush;
            }
        }
        
        #endregion

        #region WebSocket Communication
        
        private async void ConnectToGuardianSystem()
        {
            try
            {
                cancellationTokenSource = new CancellationTokenSource();
                webSocket = new ClientWebSocket();
                
                await webSocket.ConnectAsync(new Uri(WebSocketUrl), cancellationTokenSource.Token);
                isConnected = true;
                
                // Start listening for messages
                _ = Task.Run(ListenForMessages, cancellationTokenSource.Token);
                
                Print("Connected to Guardian System");
            }
            catch (Exception ex)
            {
                Print($"Failed to connect to Guardian System: {ex.Message}");
                isConnected = false;
            }
        }
        
        private async Task ListenForMessages()
        {
            var buffer = new byte[1024 * 4];
            
            try
            {
                while (webSocket.State == WebSocketState.Open && !cancellationTokenSource.Token.IsCancellationRequested)
                {
                    var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationTokenSource.Token);
                    
                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        ProcessGuardianMessage(message);
                    }
                }
            }
            catch (Exception ex)
            {
                Print($"WebSocket error: {ex.Message}");
                isConnected = false;
            }
        }
        
        private void ProcessGuardianMessage(string jsonMessage)
        {
            try
            {
                dynamic message = JsonConvert.DeserializeObject(jsonMessage);
                string messageType = message.type;
                
                switch (messageType)
                {
                    case "enigma_update":
                        UpdateEnigmaData(message.data);
                        break;
                    case "kelly_update":
                        UpdateKellyData(message.data);
                        break;
                    case "compliance_update":
                        UpdateComplianceData(message.data);
                        break;
                    case "emergency_stop":
                        HandleEmergencyStop(message.data);
                        break;
                }
            }
            catch (Exception ex)
            {
                Print($"Error processing Guardian message: {ex.Message}");
            }
        }
        
        private void UpdateEnigmaData(dynamic data)
        {
            if (data.enigma_data != null)
            {
                enigmaPowerScore = data.enigma_data.power_score ?? 0;
                enigmaConfluence = data.enigma_data.confluence_level ?? "L1";
                enigmaSignalColor = data.enigma_data.signal_color ?? "NEUTRAL";
                macvuState = data.enigma_data.macvu_state ?? "NEUTRAL";
            }
        }
        
        private void UpdateKellyData(dynamic data)
        {
            if (data.kelly_data != null)
            {
                kellyPercentage = data.kelly_data.half_kelly_percentage ?? 0;
                recommendedSize = data.kelly_data.position_size ?? 0;
            }
        }
        
        private void UpdateComplianceData(dynamic data)
        {
            if (data.compliance_data != null)
            {
                complianceGreen = data.compliance_data.overall_level == "safe";
                complianceMessage = data.compliance_data.overall_level ?? "Unknown";
                tradingEnabled = data.compliance_data.trading_enabled ?? false;
            }
        }
        
        private void HandleEmergencyStop(dynamic data)
        {
            emergencyStop = true;
            tradingEnabled = false;
            Print($"EMERGENCY STOP: {data.reason}");
        }
        
        private void DisconnectFromGuardianSystem()
        {
            try
            {
                if (cancellationTokenSource != null)
                {
                    cancellationTokenSource.Cancel();
                }
                
                if (webSocket != null && webSocket.State == WebSocketState.Open)
                {
                    webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Indicator closing", CancellationToken.None);
                }
                
                isConnected = false;
            }
            catch (Exception ex)
            {
                Print($"Error disconnecting: {ex.Message}");
            }
        }
        
        #endregion

        #region Properties
        
        [NinjaScriptProperty]
        [Display(Name = "WebSocket URL", Description = "Guardian WebSocket server URL", Order = 1, GroupName = "Connection")]
        public string WebSocketUrl { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Auto Connect", Description = "Automatically connect to Guardian system", Order = 2, GroupName = "Connection")]
        public bool AutoConnect { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Show Enigma Panel", Description = "Display Enigma signals panel", Order = 3, GroupName = "Display")]
        public bool ShowEnigmaPanel { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Show Kelly Panel", Description = "Display Kelly position sizing panel", Order = 4, GroupName = "Display")]
        public bool ShowKellyPanel { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Show Compliance Panel", Description = "Display Apex compliance panel", Order = 5, GroupName = "Display")]
        public bool ShowCompliancePanel { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Show Control Panel", Description = "Display trading control panel", Order = 6, GroupName = "Display")]
        public bool ShowControlPanel { get; set; }
        
        #endregion
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
    public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
    {
        private EnigmaApexGuardian[] cacheEnigmaApexGuardian;
        public EnigmaApexGuardian EnigmaApexGuardian()
        {
            return EnigmaApexGuardian(Input);
        }

        public EnigmaApexGuardian EnigmaApexGuardian(ISeries<double> input)
        {
            if (cacheEnigmaApexGuardian != null)
                for (int idx = 0; idx < cacheEnigmaApexGuardian.Length; idx++)
                    if (cacheEnigmaApexGuardian[idx] != null && cacheEnigmaApexGuardian[idx].EqualsInput(input))
                        return cacheEnigmaApexGuardian[idx];
            return CacheIndicator<EnigmaApexGuardian>(new EnigmaApexGuardian(), input, ref cacheEnigmaApexGuardian);
        }
    }
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
    public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
    {
        public Indicators.EnigmaApexGuardian EnigmaApexGuardian()
        {
            return indicator.EnigmaApexGuardian(Input);
        }

        public Indicators.EnigmaApexGuardian EnigmaApexGuardian(ISeries<double> input)
        {
            return indicator.EnigmaApexGuardian(input);
        }
    }
}

namespace NinjaTrader.NinjaScript.Strategies
{
    public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
    {
        public Indicators.EnigmaApexGuardian EnigmaApexGuardian()
        {
            return indicator.EnigmaApexGuardian(Input);
        }

        public Indicators.EnigmaApexGuardian EnigmaApexGuardian(ISeries<double> input)
        {
            return indicator.EnigmaApexGuardian(input);
        }
    }
}

#endregion
