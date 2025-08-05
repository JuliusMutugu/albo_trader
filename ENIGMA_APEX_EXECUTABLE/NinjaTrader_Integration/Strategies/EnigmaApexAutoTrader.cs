
// ============================================
// ENIGMA-APEX AUTO TRADER STRATEGY
// Automated execution with ChatGPT guidance
// ============================================

using System;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.NinjaScript.Strategies
{
    public class EnigmaApexAutoTrader : Strategy
    {
        private double lastPowerScore = 0;
        private string lastConfluenceLevel = "";
        private bool isGuardianConnected = false;
        
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Enigma-Apex Automated Trading with ChatGPT Integration";
                Name = "EnigmaApexAutoTrader";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 0;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 20;
                IsInstantiatedOnEachOptimizationIteration = true;
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade)
                return;
                
            // Get signal from Guardian Agent (WebSocket connection)
            var signal = GetGuardianSignal();
            
            if (signal != null && signal.Action == "TRADE")
            {
                ProcessTradeSignal(signal);
            }
        }
        
        private void ProcessTradeSignal(GuardianSignal signal)
        {
            if (Position.MarketPosition == MarketPosition.Flat)
            {
                // Calculate position size using Kelly criterion
                int quantity = CalculatePositionSize(signal.KellyFraction);
                
                // Validate with risk manager
                if (ValidateWithRiskManager(quantity))
                {
                    if (signal.Direction == "LONG")
                    {
                        EnterLong(quantity, "EnigmaLong");
                        SetStopLoss("EnigmaLong", CalculationMode.Price, 
                            Close[0] - (ATR(14)[0] * 1.5));
                        SetProfitTarget("EnigmaLong", CalculationMode.Price, 
                            Close[0] + (ATR(14)[0] * 2.0));
                    }
                    else if (signal.Direction == "SHORT")
                    {
                        EnterShort(quantity, "EnigmaShort");
                        SetStopLoss("EnigmaShort", CalculationMode.Price, 
                            Close[0] + (ATR(14)[0] * 1.5));
                        SetProfitTarget("EnigmaShort", CalculationMode.Price, 
                            Close[0] - (ATR(14)[0] * 2.0));
                    }
                    
                    Print($"Trade executed: {signal.Direction} {quantity} contracts " +
                          $"(Power: {signal.PowerScore}, Level: {signal.ConfluenceLevel})");
                }
            }
        }
        
        private GuardianSignal GetGuardianSignal()
        {
            // WebSocket connection to Guardian Agent would be implemented here
            // For demo, return mock signal
            return new GuardianSignal
            {
                Action = "TRADE",
                Direction = "LONG",
                PowerScore = 22,
                ConfluenceLevel = "L3",
                KellyFraction = 0.021,
                Confidence = 0.78
            };
        }
        
        private int CalculatePositionSize(double kellyFraction)
        {
            double accountValue = Account.Get(AccountItem.CashValue, Currency.UsDollar);
            double maxRisk = accountValue * kellyFraction;
            double pointValue = MasterInstrument.PointValue;
            double atr = ATR(14)[0];
            
            return (int)(maxRisk / (atr * pointValue));
        }
        
        private bool ValidateWithRiskManager(int quantity)
        {
            // Integration with Risk Manager AddOn
            return true; // Simplified for demo
        }
    }
    
    public class GuardianSignal
    {
        public string Action { get; set; }
        public string Direction { get; set; }
        public int PowerScore { get; set; }
        public string ConfluenceLevel { get; set; }
        public double KellyFraction { get; set; }
        public double Confidence { get; set; }
    }
}
