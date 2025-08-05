
// ============================================
// ENIGMA-APEX RISK MANAGER
// Apex Prop Firm Compliance & Kelly Sizing
// ============================================

using System;
using System.Windows.Controls;
using NinjaTrader.Cbi;
using NinjaTrader.Gui.Tools;

namespace NinjaTrader.NinjaScript.AddOns
{
    public class EnigmaApexRiskManager : AddOnBase
    {
        private double maxDailyLoss = 2500; // Apex limit
        private double maxTotalLoss = 5000; // Apex limit
        private double currentDayPnL = 0;
        private double accountBalance = 100000;
        
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Enigma-Apex Risk Manager for Apex Compliance";
                Name = "EnigmaApexRiskManager";
            }
        }
        
        public bool ValidateTradeSize(double proposedSize, string instrument)
        {
            // Kelly Criterion validation
            double kellySize = CalculateKellySize();
            double maxAllowedSize = accountBalance * kellySize;
            
            if (proposedSize > maxAllowedSize)
            {
                LogMessage($"Trade rejected: Size {proposedSize} exceeds Kelly limit {maxAllowedSize}");
                return false;
            }
            
            // Apex compliance check
            if (currentDayPnL <= -maxDailyLoss)
            {
                LogMessage("Trade rejected: Daily loss limit reached");
                return false;
            }
            
            return true;
        }
        
        private double CalculateKellySize()
        {
            // Real-time Kelly calculation from Guardian Agent
            return 0.02; // 2% default
        }
        
        private void LogMessage(string message)
        {
            NinjaTrader.Code.Output.Process($"[ENIGMA-APEX] {DateTime.Now:HH:mm:ss} {message}", 
                PrintTo.OutputTab1);
        }
    }
}
