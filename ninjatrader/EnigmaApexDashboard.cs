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
using NinjaTrader.NinjaScript.AddOns;
using System.Windows.Controls;
using System.Net.WebSockets;
using System.Text.Json;
using System.Threading;
#endregion

//This namespace holds Add ons in this folder and is required. Do not change it. 
namespace NinjaTrader.NinjaScript.AddOns
{
    public class EnigmaApexDashboard : AddOnBase
    {
        #region Variables
        private ClientWebSocket webSocket;
        private CancellationTokenSource cancellationTokenSource;
        private bool isConnected = false;

        // Dashboard data
        private string powerScore = "0";
        private string confluenceLevel = "L1";
        private string signalColor = "NEUTRAL";
        private string macvuState = "NEUTRAL";
        private string serverStatus = "Disconnected";

        // UI Elements
        private Grid dashboardGrid;
        private TextBlock powerScoreText;
        private TextBlock confluenceText;
        private TextBlock signalColorText;
        private TextBlock macvuStateText;
        private TextBlock statusText;
        private Border dashboardBorder;
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Enigma-Apex Trading Dashboard - Real-time AlgoBox Enigma signals for prop trading";
                Name = "EnigmaApexDashboard";
            }
            else if (State == State.Active)
            {
                // Create the dashboard UI
                CreateDashboard();

                // Connect to WebSocket server
                ConnectToWebSocket();
            }
            else if (State == State.Terminated)
            {
                // Clean up WebSocket connection
                DisconnectWebSocket();

                // Clean up UI
                if (dashboardBorder != null)
                {
                    // Remove from NinjaTrader UI
                    Application.Current.Dispatcher.BeginInvoke(new Action(() =>
                    {
                        var mainWindow = Application.Current.MainWindow;
                        if (mainWindow != null)
                        {
                            var grid = mainWindow.FindName("MainGrid") as Grid;
                            if (grid != null && grid.Children.Contains(dashboardBorder))
                            {
                                grid.Children.Remove(dashboardBorder);
                            }
                        }
                    }));
                }
            }
        }

        private void CreateDashboard()
        {
            Application.Current.Dispatcher.BeginInvoke(new Action(() =>
            {
                try
                {
                    // Create main dashboard border
                    dashboardBorder = new Border
                    {
                        Background = new SolidColorBrush(Color.FromRgb(30, 30, 30)),
                        BorderBrush = new SolidColorBrush(Color.FromRgb(0, 120, 215)),
                        BorderThickness = new Thickness(2),
                        CornerRadius = new CornerRadius(5),
                        Margin = new Thickness(10),
                        HorizontalAlignment = HorizontalAlignment.Right,
                        VerticalAlignment = VerticalAlignment.Top,
                        Width = 250,
                        Height = 200
                    };

                    // Create grid for layout
                    dashboardGrid = new Grid();
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });
                    dashboardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(30) });

                    // Title
                    var title = new TextBlock
                    {
                        Text = "ENIGMA-APEX DASHBOARD",
                        Foreground = new SolidColorBrush(Color.FromRgb(0, 120, 215)),
                        FontWeight = FontWeights.Bold,
                        FontSize = 12,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        Margin = new Thickness(5, 2, 5, 2)
                    };
                    Grid.SetRow(title, 0);
                    dashboardGrid.Children.Add(title);

                    // Power Score
                    powerScoreText = new TextBlock
                    {
                        Text = "Power Score: 0",
                        Foreground = new SolidColorBrush(Colors.White),
                        FontSize = 11,
                        Margin = new Thickness(10, 2, 5, 2)
                    };
                    Grid.SetRow(powerScoreText, 1);
                    dashboardGrid.Children.Add(powerScoreText);

                    // Confluence Level
                    confluenceText = new TextBlock
                    {
                        Text = "Confluence: L1",
                        Foreground = new SolidColorBrush(Colors.White),
                        FontSize = 11,
                        Margin = new Thickness(10, 2, 5, 2)
                    };
                    Grid.SetRow(confluenceText, 2);
                    dashboardGrid.Children.Add(confluenceText);

                    // Signal Color
                    signalColorText = new TextBlock
                    {
                        Text = "Signal: NEUTRAL",
                        Foreground = new SolidColorBrush(Colors.Yellow),
                        FontSize = 11,
                        Margin = new Thickness(10, 2, 5, 2)
                    };
                    Grid.SetRow(signalColorText, 3);
                    dashboardGrid.Children.Add(signalColorText);

                    // MACVU State
                    macvuStateText = new TextBlock
                    {
                        Text = "MACVU: NEUTRAL",
                        Foreground = new SolidColorBrush(Colors.White),
                        FontSize = 11,
                        Margin = new Thickness(10, 2, 5, 2)
                    };
                    Grid.SetRow(macvuStateText, 4);
                    dashboardGrid.Children.Add(macvuStateText);

                    // Status
                    statusText = new TextBlock
                    {
                        Text = "Status: Connecting...",
                        Foreground = new SolidColorBrush(Colors.Orange),
                        FontSize = 10,
                        Margin = new Thickness(10, 2, 5, 2)
                    };
                    Grid.SetRow(statusText, 5);
                    dashboardGrid.Children.Add(statusText);

                    dashboardBorder.Child = dashboardGrid;

                    // Add to main window
                    var mainWindow = Application.Current.MainWindow;
                    if (mainWindow != null)
                    {
                        var mainGrid = mainWindow.Content as Grid;
                        if (mainGrid == null)
                        {
                            // If no grid exists, try to find one or create a panel
                            var panel = mainWindow.Content as Panel;
                            if (panel != null)
                            {
                                panel.Children.Add(dashboardBorder);
                            }
                            else
                            {
                                // Create a new grid to hold the dashboard
                                var newGrid = new Grid();
                                newGrid.Children.Add(mainWindow.Content as UIElement);
                                newGrid.Children.Add(dashboardBorder);
                                mainWindow.Content = newGrid;
                            }
                        }
                        else
                        {
                            mainGrid.Children.Add(dashboardBorder);
                        }
                    }

                    NinjaTrader.Code.Output.Process("Enigma-Apex Dashboard UI created successfully", PrintTo.OutputTab1);
                }
                catch (Exception ex)
                {
                    NinjaTrader.Code.Output.Process($"Error creating dashboard UI: {ex.Message}", PrintTo.OutputTab1);
                }
            }));
        }

        private async void ConnectToWebSocket()
        {
            try
            {
                webSocket = new ClientWebSocket();
                cancellationTokenSource = new CancellationTokenSource();

                // Connect to your Enigma-Apex WebSocket server
                var uri = new Uri("ws://localhost:8765/ninja");
                await webSocket.ConnectAsync(uri, cancellationTokenSource.Token);

                isConnected = true;
                UpdateStatus("Connected", Colors.Green);

                // Send identification
                await SendIdentification();

                // Start listening for messages
                _ = Task.Run(async () => await ListenForMessages());

                // Start heartbeat
                _ = Task.Run(async () => await SendHeartbeat());

                NinjaTrader.Code.Output.Process("Connected to Enigma-Apex WebSocket server", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                isConnected = false;
                UpdateStatus("Connection Failed", Colors.Red);
                NinjaTrader.Code.Output.Process($"WebSocket connection error: {ex.Message}", PrintTo.OutputTab1);
            }
        }

        private async Task SendIdentification()
        {
            if (!isConnected) return;

            try
            {
                var identification = new
                {
                    type = "client_identification",
                    data = new
                    {
                        client_type = "ninja_dashboard",
                        version = "1.0.0",
                        platform = "NinjaTrader 8"
                    }
                };

                var json = JsonSerializer.Serialize(identification);
                var bytes = Encoding.UTF8.GetBytes(json);
                await webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, cancellationTokenSource.Token);

                NinjaTrader.Code.Output.Process("Sent identification to Enigma-Apex server", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                NinjaTrader.Code.Output.Process($"Error sending identification: {ex.Message}", PrintTo.OutputTab1);
            }
        }

        private async Task ListenForMessages()
        {
            var buffer = new byte[4096];

            while (isConnected && webSocket.State == WebSocketState.Open)
            {
                try
                {
                    var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationTokenSource.Token);

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        var json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        ProcessMessage(json);
                    }
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    NinjaTrader.Code.Output.Process($"Error receiving message: {ex.Message}", PrintTo.OutputTab1);
                    break;
                }
            }
        }

        private void ProcessMessage(string json)
        {
            try
            {
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    var messageType = root.GetProperty("type").GetString();

                    if (messageType == "status_request" && root.TryGetProperty("data", out var data))
                    {
                        // Update dashboard with Enigma data
                        if (data.TryGetProperty("enigma_data", out var enigmaData))
                        {
                            var powerScore = enigmaData.TryGetProperty("power_score", out var ps) ? ps.GetInt32().ToString() : "0";
                            var confluence = enigmaData.TryGetProperty("confluence_level", out var cl) ? cl.GetString() : "L1";
                            var signalColor = enigmaData.TryGetProperty("signal_color", out var sc) ? sc.GetString() : "NEUTRAL";
                            var macvuState = enigmaData.TryGetProperty("macvu_state", out var ms) ? ms.GetString() : "NEUTRAL";

                            UpdateDashboard(powerScore, confluence, signalColor, macvuState);
                        }
                    }
                    else if (messageType == "enigma_update" && root.TryGetProperty("data", out var updateData))
                    {
                        // Handle real-time Enigma updates
                        var powerScore = updateData.TryGetProperty("power_score", out var ps) ? ps.GetInt32().ToString() : this.powerScore;
                        var confluence = updateData.TryGetProperty("confluence_level", out var cl) ? cl.GetString() : this.confluenceLevel;
                        var signalColor = updateData.TryGetProperty("signal_color", out var sc) ? sc.GetString() : this.signalColor;
                        var macvuState = updateData.TryGetProperty("macvu_state", out var ms) ? ms.GetString() : this.macvuState;

                        UpdateDashboard(powerScore, confluence, signalColor, macvuState);
                    }
                }
            }
            catch (Exception ex)
            {
                NinjaTrader.Code.Output.Process($"Error processing message: {ex.Message}", PrintTo.OutputTab1);
            }
        }

        private void UpdateDashboard(string powerScore, string confluence, string signalColor, string macvuState)
        {
            Application.Current.Dispatcher.BeginInvoke(new Action(() =>
            {
                try
                {
                    this.powerScore = powerScore;
                    this.confluenceLevel = confluence;
                    this.signalColor = signalColor;
                    this.macvuState = macvuState;

                    if (powerScoreText != null)
                        powerScoreText.Text = $"Power Score: {powerScore}";

                    if (confluenceText != null)
                        confluenceText.Text = $"Confluence: {confluence}";

                    if (signalColorText != null)
                    {
                        signalColorText.Text = $"Signal: {signalColor}";

                        // Update color based on signal
                        switch (signalColor.ToUpper())
                        {
                            case "GREEN":
                                signalColorText.Foreground = new SolidColorBrush(Colors.Green);
                                break;
                            case "RED":
                                signalColorText.Foreground = new SolidColorBrush(Colors.Red);
                                break;
                            case "YELLOW":
                                signalColorText.Foreground = new SolidColorBrush(Colors.Yellow);
                                break;
                            default:
                                signalColorText.Foreground = new SolidColorBrush(Colors.White);
                                break;
                        }
                    }

                    if (macvuStateText != null)
                        macvuStateText.Text = $"MACVU: {macvuState}";
                }
                catch (Exception ex)
                {
                    NinjaTrader.Code.Output.Process($"Error updating dashboard: {ex.Message}", PrintTo.OutputTab1);
                }
            }));
        }

        private void UpdateStatus(string status, Color color)
        {
            Application.Current.Dispatcher.BeginInvoke(new Action(() =>
            {
                if (statusText != null)
                {
                    statusText.Text = $"Status: {status}";
                    statusText.Foreground = new SolidColorBrush(color);
                }
            }));
        }

        private async Task SendHeartbeat()
        {
            while (isConnected && webSocket.State == WebSocketState.Open)
            {
                try
                {
                    var heartbeat = new
                    {
                        type = "heartbeat",
                        data = new { message = "ninja_ping" },
                        timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
                    };

                    var json = JsonSerializer.Serialize(heartbeat);
                    var bytes = Encoding.UTF8.GetBytes(json);
                    await webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, cancellationTokenSource.Token);

                    await Task.Delay(30000, cancellationTokenSource.Token); // Send heartbeat every 30 seconds
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    NinjaTrader.Code.Output.Process($"Heartbeat error: {ex.Message}", PrintTo.OutputTab1);
                    break;
                }
            }
        }

        private void DisconnectWebSocket()
        {
            try
            {
                isConnected = false;
                cancellationTokenSource?.Cancel();

                if (webSocket != null && webSocket.State == WebSocketState.Open)
                {
                    webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                }

                webSocket?.Dispose();
                cancellationTokenSource?.Dispose();

                UpdateStatus("Disconnected", Colors.Gray);
                NinjaTrader.Code.Output.Process("Disconnected from Enigma-Apex server", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                NinjaTrader.Code.Output.Process($"Error disconnecting: {ex.Message}", PrintTo.OutputTab1);
            }
        }
    }
}
