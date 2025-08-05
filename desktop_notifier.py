"""
Desktop Notification System for Enigma-Apex
Cross-platform desktop notifications for trading signals
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Cross-platform notification libraries
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("⚠️  Plyer not installed. Install with: pip install plyer")

try:
    import win10toast
    WIN10_TOAST_AVAILABLE = True
except ImportError:
    WIN10_TOAST_AVAILABLE = False

# Windows-specific notifications
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DesktopNotifier:
    """
    Cross-platform desktop notification system for Enigma-Apex
    Supports Windows, macOS, and Linux with multiple notification methods
    """
    
    def __init__(self):
        self.app_name = "Enigma-Apex"
        self.app_icon = self._get_icon_path()
        self.notification_history = []
        self.sound_enabled = True
        self.max_history = 100
        
        # Initialize Windows toast notifier if available
        self.win_toast = None
        if WIN10_TOAST_AVAILABLE:
            self.win_toast = win10toast.ToastNotifier()
        
        logger.info("DesktopNotifier initialized")
        self._log_available_features()
    
    def _get_icon_path(self) -> str:
        """Get the path to the notification icon"""
        # You can place an icon file in your project directory
        icon_paths = [
            "assets/enigma_icon.ico",
            "assets/icon.ico", 
            "icon.ico",
            None  # Fallback to no icon
        ]
        
        for path in icon_paths:
            if path and self._file_exists(path):
                return path
        
        return None
    
    def _file_exists(self, path: str) -> bool:
        """Check if file exists"""
        try:
            import os
            return os.path.exists(path)
        except:
            return False
    
    def _log_available_features(self):
        """Log which notification features are available"""
        features = []
        if PLYER_AVAILABLE:
            features.append("Plyer (cross-platform)")
        if WIN10_TOAST_AVAILABLE:
            features.append("Windows 10 Toast")
        if WINSOUND_AVAILABLE:
            features.append("Windows Sound")
        
        logger.info(f"Available notification features: {', '.join(features) if features else 'None'}")
    
    def _play_notification_sound(self, sound_type: str = "signal"):
        """Play notification sound"""
        if not self.sound_enabled or not WINSOUND_AVAILABLE:
            return
        
        try:
            if sound_type == "signal":
                # Standard Windows notification sound
                winsound.MessageBeep(0x00000040)  # MB_ICONINFORMATION
            elif sound_type == "critical":
                # Critical alert sound
                winsound.MessageBeep(0x00000030)  # MB_ICONEXCLAMATION
            elif sound_type == "error":
                # Error sound
                winsound.MessageBeep(0x00000010)  # MB_ICONHAND
        except Exception as e:
            logger.warning(f"Could not play sound: {e}")
    
    def _format_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """Format signal data into readable notification message"""
        symbol = signal_data.get('symbol', 'Unknown')
        signal_type = signal_data.get('type', 'Signal')
        power_score = signal_data.get('power_score', 0)
        direction = signal_data.get('direction', 'Unknown')
        timestamp = signal_data.get('timestamp', '')
        
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        elif isinstance(timestamp, str) and timestamp:
            # Parse timestamp if it's a string
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%H:%M:%S')
            except:
                timestamp = timestamp[:8] if len(timestamp) > 8 else timestamp
        
        message = f"""Symbol: {symbol}
Power Score: {power_score}
Direction: {direction}
Time: {timestamp}"""
        
        return message
    
    def _get_notification_priority(self, signal_data: Dict[str, Any]) -> str:
        """Determine notification priority based on signal data"""
        power_score = signal_data.get('power_score', 0)
        
        if power_score >= 90:
            return "critical"
        elif power_score >= 75:
            return "high"
        elif power_score >= 50:
            return "medium"
        else:
            return "low"
    
    async def send_signal_notification(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send desktop notification for new Enigma signal
        
        Args:
            signal_data: Dictionary containing signal information
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            signal_type = signal_data.get('type', 'Signal')
            symbol = signal_data.get('symbol', 'Unknown')
            power_score = signal_data.get('power_score', 0)
            priority = self._get_notification_priority(signal_data)
            
            # Create notification title
            title = f"🎯 Enigma {signal_type} - {symbol}"
            if power_score >= 80:
                title = f"🔥 {title} (High Power!)"
            
            # Create message
            message = self._format_signal_message(signal_data)
            
            # Send notification using best available method
            success = await self._send_notification(
                title=title,
                message=message,
                priority=priority,
                notification_type="signal"
            )
            
            # Log notification
            self._log_notification(signal_data, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send signal notification: {e}")
            return False
    
    async def send_trade_notification(self, trade_data: Dict[str, Any], alert_type: str) -> bool:
        """
        Send notification for trade events (entry, exit, stop loss)
        
        Args:
            trade_data: Dictionary containing trade information
            alert_type: Type of trade alert (entry, exit, stop_loss)
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            symbol = trade_data.get('symbol', 'Unknown')
            action = trade_data.get('action', alert_type)
            price = trade_data.get('price', 0)
            quantity = trade_data.get('quantity', 0)
            
            # Create notification based on alert type
            if alert_type == "entry":
                title = f"📈 Trade Entry - {symbol}"
                emoji = "📈"
            elif alert_type == "exit":
                title = f"📊 Trade Exit - {symbol}"
                emoji = "📊"
            elif alert_type == "stop_loss":
                title = f"🛑 Stop Loss - {symbol}"
                emoji = "🛑"
            else:
                title = f"💼 Trade Alert - {symbol}"
                emoji = "💼"
            
            message = f"""{emoji} {action.title()}
Symbol: {symbol}
Price: ${price}
Quantity: {quantity}
Time: {datetime.now().strftime('%H:%M:%S')}"""
            
            # Send notification
            success = await self._send_notification(
                title=title,
                message=message,
                priority="high" if alert_type == "stop_loss" else "medium",
                notification_type="trade"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}")
            return False
    
    async def send_risk_notification(self, risk_data: Dict[str, Any], severity: str) -> bool:
        """
        Send notification for risk management alerts
        
        Args:
            risk_data: Dictionary containing risk information
            severity: Risk severity level (low, medium, high, critical)
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            risk_type = risk_data.get('type', 'Risk Alert')
            message_text = risk_data.get('message', 'Risk management alert')
            account_value = risk_data.get('account_value', 0)
            drawdown = risk_data.get('drawdown_percent', 0)
            
            # Create notification based on severity
            severity_emojis = {
                "low": "⚠️",
                "medium": "🟡",
                "high": "🟠", 
                "critical": "🔴"
            }
            
            emoji = severity_emojis.get(severity, "⚠️")
            title = f"{emoji} Risk Alert - {risk_type}"
            
            message = f"""{emoji} {message_text}
Account: ${account_value:,.2f}
Drawdown: {drawdown:.1f}%
Time: {datetime.now().strftime('%H:%M:%S')}"""
            
            # Send notification
            success = await self._send_notification(
                title=title,
                message=message,
                priority=severity,
                notification_type="risk"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send risk notification: {e}")
            return False
    
    async def send_system_notification(self, title: str, message: str, notification_type: str = "info") -> bool:
        """
        Send general system notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Add emoji based on type
            type_emojis = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅"
            }
            
            emoji = type_emojis.get(notification_type, "ℹ️")
            full_title = f"{emoji} {title}"
            
            # Send notification
            success = await self._send_notification(
                title=full_title,
                message=message,
                priority="medium" if notification_type == "warning" else "low",
                notification_type="system"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
            return False
    
    async def _send_notification(self, title: str, message: str, priority: str, notification_type: str) -> bool:
        """
        Internal method to send notification using best available method
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, critical)
            notification_type: Type of notification
            
        Returns:
            bool: True if notification was sent successfully
        """
        success = False
        
        # Try Windows 10 Toast notification first (most modern)
        if WIN10_TOAST_AVAILABLE and self.win_toast:
            try:
                duration = 10 if priority in ["high", "critical"] else 5
                
                self.win_toast.show_toast(
                    title=title,
                    msg=message,
                    icon_path=self.app_icon,
                    duration=duration,
                    threaded=True
                )
                success = True
                logger.info(f"Sent Windows 10 toast notification: {title}")
                
            except Exception as e:
                logger.warning(f"Windows 10 toast failed: {e}")
        
        # Fallback to Plyer (cross-platform)
        if not success and PLYER_AVAILABLE:
            try:
                timeout = 15 if priority in ["high", "critical"] else 8
                
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    app_icon=self.app_icon,
                    timeout=timeout,
                    toast=True
                )
                success = True
                logger.info(f"Sent Plyer notification: {title}")
                
            except Exception as e:
                logger.warning(f"Plyer notification failed: {e}")
        
        # Play sound for important notifications
        if success and priority in ["high", "critical"]:
            sound_type = "critical" if priority == "critical" else "signal"
            self._play_notification_sound(sound_type)
        
        # Final fallback - console notification
        if not success:
            self._console_notification(title, message)
            success = True  # Console notification always "succeeds"
        
        return success
    
    def _console_notification(self, title: str, message: str):
        """Fallback console notification when GUI notifications aren't available"""
        print("\n" + "=" * 50)
        print(f"🔔 {title}")
        print("-" * 50)
        print(message)
        print("=" * 50)
        logger.info(f"Console notification: {title}")
    
    def _log_notification(self, signal_data: Dict[str, Any], success: bool):
        """Log notification to history"""
        notification_record = {
            'timestamp': datetime.now().isoformat(),
            'signal_data': signal_data,
            'success': success,
            'symbol': signal_data.get('symbol', 'Unknown'),
            'power_score': signal_data.get('power_score', 0)
        }
        
        self.notification_history.append(notification_record)
        
        # Keep only recent notifications
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        if not self.notification_history:
            return {
                'total_sent': 0,
                'success_rate': 0,
                'average_power_score': 0,
                'recent_notifications': []
            }
        
        total_sent = len(self.notification_history)
        successful = sum(1 for n in self.notification_history if n['success'])
        success_rate = (successful / total_sent) * 100 if total_sent > 0 else 0
        
        power_scores = [n['signal_data'].get('power_score', 0) for n in self.notification_history]
        avg_power_score = sum(power_scores) / len(power_scores) if power_scores else 0
        
        recent_notifications = self.notification_history[-10:]  # Last 10 notifications
        
        return {
            'total_sent': total_sent,
            'success_rate': success_rate,
            'average_power_score': avg_power_score,
            'recent_notifications': recent_notifications
        }
    
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable notification sounds"""
        self.sound_enabled = enabled
        logger.info(f"Notification sounds {'enabled' if enabled else 'disabled'}")


# Test function
async def test_desktop_notifications():
    """Test desktop notification functionality"""
    print("🧪 Testing Desktop Notifications")
    print("=" * 40)
    
    notifier = DesktopNotifier()
    
    # Test signal notification
    test_signal = {
        'symbol': 'EURUSD',
        'type': 'L3',
        'power_score': 85,
        'direction': 'BUY',
        'timestamp': time.time()
    }
    
    print("📤 Sending test signal notification...")
    success = await notifier.send_signal_notification(test_signal)
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Test trade notification
    test_trade = {
        'symbol': 'EURUSD',
        'action': 'BUY',
        'price': 1.0850,
        'quantity': 1000
    }
    
    print("📤 Sending test trade notification...")
    success = await notifier.send_trade_notification(test_trade, "entry")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Test risk notification
    test_risk = {
        'type': 'Drawdown Warning',
        'message': 'Account drawdown approaching 5% limit',
        'account_value': 50000,
        'drawdown_percent': 4.8
    }
    
    print("📤 Sending test risk notification...")
    success = await notifier.send_risk_notification(test_risk, "high")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Get stats
    stats = notifier.get_notification_stats()
    print(f"\n📊 Notification Stats:")
    print(f"Total sent: {stats['total_sent']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average power score: {stats['average_power_score']:.1f}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_desktop_notifications())
