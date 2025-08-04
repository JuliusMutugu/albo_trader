"""
Mobile API server for remote trading control.

This module provides a secure REST API for mobile devices to control
the trading system remotely.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    # Fallback for basic HTTP server if FastAPI not available
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading


class MobileAPIServer:
    """
    Mobile API server for remote trading control.
    
    Features:
    - Secure authentication
    - Trading enable/disable
    - System status monitoring
    - Account information
    - Emergency controls
    """
    
    def __init__(self, config: Dict[str, Any], guardian_engine):
        self.config = config
        self.guardian_engine = guardian_engine
        self.logger = logging.getLogger(__name__)
        
        # Server configuration
        self.host = config.get('api_host', '0.0.0.0')
        self.port = config.get('api_port', 8000)
        self.auth_token = config.get('auth_token', 'change_this_token')
        
        # FastAPI app
        self.app = None
        self.server = None
        
        self._setup_api()
        
    def _setup_api(self):
        """Setup FastAPI application with endpoints."""
        try:
            self.app = FastAPI(
                title="Enigma-Apex Mobile API",
                description="Remote trading control API",
                version="1.0.0"
            )
            
            # CORS middleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Security
            security = HTTPBearer()
            
            def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
                if credentials.credentials != self.auth_token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication token"
                    )
                return credentials.credentials
                
            # API Endpoints
            @self.app.get("/")
            async def root():
                return {"message": "Enigma-Apex Mobile API", "status": "active"}
                
            @self.app.get("/status")
            async def get_status(token: str = Depends(verify_token)):
                """Get comprehensive system status."""
                try:
                    status = self.guardian_engine.get_system_status()
                    return {"success": True, "data": status}
                except Exception as e:
                    self.logger.error(f"Status request error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.post("/trading/enable")
            async def enable_trading(token: str = Depends(verify_token)):
                """Enable trading system."""
                try:
                    success = self.guardian_engine.enable_trading()
                    return {
                        "success": success,
                        "message": "Trading enabled" if success else "Failed to enable trading"
                    }
                except Exception as e:
                    self.logger.error(f"Enable trading error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.post("/trading/disable")
            async def disable_trading(token: str = Depends(verify_token)):
                """Disable trading system."""
                try:
                    success = self.guardian_engine.disable_trading()
                    return {
                        "success": success,
                        "message": "Trading disabled" if success else "Failed to disable trading"
                    }
                except Exception as e:
                    self.logger.error(f"Disable trading error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.post("/emergency/stop")
            async def emergency_stop(token: str = Depends(verify_token)):
                """Emergency stop all trading."""
                try:
                    # Disable trading
                    self.guardian_engine.disable_trading()
                    
                    # Close any open positions
                    if hasattr(self.guardian_engine, 'ninjatrader_client'):
                        await self.guardian_engine.ninjatrader_client.close_position()
                        
                    return {"success": True, "message": "Emergency stop executed"}
                    
                except Exception as e:
                    self.logger.error(f"Emergency stop error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.get("/account/status")
            async def get_account_status(token: str = Depends(verify_token)):
                """Get Apex account status."""
                try:
                    if hasattr(self.guardian_engine, 'apex_monitor'):
                        status = self.guardian_engine.apex_monitor.get_status()
                        return {"success": True, "data": status}
                    else:
                        return {"success": False, "message": "Apex monitor not available"}
                        
                except Exception as e:
                    self.logger.error(f"Account status error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.get("/kelly/stats")
            async def get_kelly_stats(token: str = Depends(verify_token)):
                """Get Kelly engine statistics."""
                try:
                    if hasattr(self.guardian_engine, 'kelly_engine'):
                        stats = self.guardian_engine.kelly_engine.get_stats()
                        return {"success": True, "data": stats}
                    else:
                        return {"success": False, "message": "Kelly engine not available"}
                        
                except Exception as e:
                    self.logger.error(f"Kelly stats error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.get("/cadence/status")
            async def get_cadence_status(token: str = Depends(verify_token)):
                """Get cadence tracker status."""
                try:
                    if hasattr(self.guardian_engine, 'cadence_tracker'):
                        status = self.guardian_engine.cadence_tracker.get_status()
                        return {"success": True, "data": status}
                    else:
                        return {"success": False, "message": "Cadence tracker not available"}
                        
                except Exception as e:
                    self.logger.error(f"Cadence status error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                    
            @self.app.get("/health")
            async def health_check():
                """Health check endpoint (no auth required)."""
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
                
        except ImportError:
            self.logger.warning("FastAPI not available, using basic HTTP server")
            self._setup_basic_server()
            
    def _setup_basic_server(self):
        """Setup basic HTTP server as fallback."""
        # Implementation for basic HTTP server if FastAPI not available
        # This would be a simplified version of the API
        pass
        
    async def start(self):
        """Start the mobile API server."""
        try:
            self.logger.info(f"Starting Mobile API server on {self.host}:{self.port}")
            
            if self.app:
                config = uvicorn.Config(
                    app=self.app,
                    host=self.host,
                    port=self.port,
                    log_level="info"
                )
                self.server = uvicorn.Server(config)
                await self.server.serve()
            else:
                self.logger.error("API server not properly configured")
                
        except Exception as e:
            self.logger.error(f"API server startup error: {e}")
            
    async def shutdown(self):
        """Shutdown the mobile API server."""
        try:
            self.logger.info("Shutting down Mobile API server...")
            
            if self.server:
                self.server.should_exit = True
                
        except Exception as e:
            self.logger.error(f"API server shutdown error: {e}")
            
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.
        
        Returns:
            Dictionary with server details
        """
        return {
            "host": self.host,
            "port": self.port,
            "auth_enabled": bool(self.auth_token),
            "endpoints": [
                "/status",
                "/trading/enable",
                "/trading/disable", 
                "/emergency/stop",
                "/account/status",
                "/kelly/stats",
                "/cadence/status",
                "/health"
            ]
        }
