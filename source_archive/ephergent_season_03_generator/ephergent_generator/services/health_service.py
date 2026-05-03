"""
Service Health Monitoring System
Monitors all services and provides health status information
"""
import time
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthService:
    """Comprehensive health monitoring system for tracking service statuses.

    This service provides detailed health checks and status monitoring for various
    system services, including Gemini AI, Character, Image, ComfyUI, Audio, Video,
    YouTube, and Ghost services.

    Key Features:
    - Lazy loading of service modules to prevent circular imports
    - Fail-safe service status checking
    - Detailed status reporting with response times and error handling
    - Quick and comprehensive health check methods

    Attributes:
        services (dict): Container for service status information
        last_check_time (datetime, optional): Timestamp of the most recent full health check

    Example:
        >>> health_service = HealthService()
        >>> status = health_service.get_all_service_status()
        >>> print(status['overall_status'])
    """
    
    def __init__(self):
        """Initialize the health monitoring service for system services.

        This constructor sets up the initial state of the health monitoring service,
        preparing it to track the status of various system services. It initializes
        an empty services dictionary and sets up references to services that will
        be lazily loaded to prevent circular imports.

        Attributes:
            services (dict): A dictionary to store service status information.
            last_check_time (datetime, optional): Timestamp of the last full health check.
        
        Logs an info message when the health monitoring service is initialized.
        """
        self.services = {}
        self.last_check_time = None
        
        # Initialize service references (imported when needed to avoid circular imports)
        self._gemini_service = None
        self._character_service = None  
        self._image_service = None
        self._comfyui_service = None
        self._audio_service = None
        self._video_service = None
        self._youtube_service = None
        self._ghost_service = None
        
        logger.info("Health monitoring service initialized")
    
    def get_all_service_status(self) -> Dict[str, Any]:
        """Perform a comprehensive health check across all system services.

        This method checks the status of each registered service, collecting
        detailed health information and generating an overall system status.

        Returns:
            Dict[str, Any]: A comprehensive health status dictionary containing:
                - timestamp: ISO format timestamp of the health check
                - overall_status: System health status (\"healthy\", \"degraded\", \"unhealthy\")
                - services: Detailed status for each service
                - summary: Aggregate service status statistics
                - check_duration_ms: Total time taken for the health check

        Example:
            >>> health_service = HealthService()
            >>> status = health_service.get_all_service_status()
            >>> print(status['overall_status'])  # Might print \"healthy\", \"degraded\", or \"unhealthy\"
        
        Notes:
            - Services are checked in a fail-safe manner
            - Any service that raises an exception is marked as an error
            - The method logs the health check process and results
        """
        start_time = time.time()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "summary": {
                "total_services": 0,
                "healthy_services": 0,
                "unhealthy_services": 0,
                "unknown_services": 0
            },
            "check_duration_ms": 0
        }
        
        # Check each service
        services_to_check = [
            ("database", self._check_database_service),
            ("gemini", self._check_gemini_service),
            ("character", self._check_character_service),
            ("image", self._check_image_service),
            ("comfyui", self._check_comfyui_service),
            ("audio", self._check_audio_service),
            ("video", self._check_video_service),
            ("youtube", self._check_youtube_service),
            ("ghost", self._check_ghost_service)
        ]
        
        for service_name, check_function in services_to_check:
            try:
                service_status = check_function()
                status["services"][service_name] = service_status
            except Exception as e:
                logger.error(f"Error checking {service_name} service: {e}")
                status["services"][service_name] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e),
                    "response_time_ms": None
                }
        
        # Calculate summary
        for service_data in status["services"].values():
            status["summary"]["total_services"] += 1
            if service_data.get("healthy", False):
                status["summary"]["healthy_services"] += 1
            elif service_data.get("status") == "unknown":
                status["summary"]["unknown_services"] += 1
            else:
                status["summary"]["unhealthy_services"] += 1
        
        # Determine overall status
        if status["summary"]["unhealthy_services"] > 0:
            status["overall_status"] = "degraded" if status["summary"]["healthy_services"] > 0 else "unhealthy"
        elif status["summary"]["unknown_services"] > 0:
            status["overall_status"] = "unknown"
        
        status["check_duration_ms"] = round((time.time() - start_time) * 1000, 2)
        self.last_check_time = datetime.now()
        
        logger.info(f"Health check completed in {status['check_duration_ms']}ms - Status: {status['overall_status']}")
        return status

    def _check_database_service(self) -> Dict[str, Any]:
        """Check database connectivity and health"""
        start_time = time.time()

        try:
            from ephergent_generator import db
            from sqlalchemy import text

            # Test database connection with a simple query
            result = db.session.execute(text('SELECT 1'))
            connected = result.scalar() == 1

            # Get connection pool stats if available
            pool_stats = {}
            if hasattr(db.engine.pool, 'size'):
                pool_stats['pool_size'] = db.engine.pool.size()
            if hasattr(db.engine.pool, 'checkedin'):
                pool_stats['connections_checkedin'] = db.engine.pool.checkedin()
            if hasattr(db.engine.pool, 'checkedout'):
                pool_stats['connections_checkedout'] = db.engine.pool.checkedout()
            if hasattr(db.engine.pool, 'overflow'):
                pool_stats['overflow'] = db.engine.pool.overflow()

            response_time = round((time.time() - start_time) * 1000, 2)

            return {
                "status": "healthy" if connected else "unhealthy",
                "healthy": connected,
                "response_time_ms": response_time,
                "details": {
                    "connected": connected,
                    "database_url": str(db.engine.url).split('@')[-1] if hasattr(db.engine, 'url') else "unknown",
                    **pool_stats
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    def _check_gemini_service(self) -> Dict[str, Any]:
        """Check Gemini AI service status"""
        start_time = time.time()
        
        try:
            if not self._gemini_service:
                from ephergent_generator.services.gemini_service import GeminiService
                self._gemini_service = GeminiService()
            
            # Check if API key is configured
            configured = self._gemini_service.client is not None
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "healthy" if configured else "misconfigured",
                "healthy": configured,
                "response_time_ms": response_time,
                "details": {
                    "api_key_configured": configured,
                    "model": self._gemini_service.model if hasattr(self._gemini_service, 'model') else "unknown"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_character_service(self) -> Dict[str, Any]:
        """Check Character service status"""
        start_time = time.time()
        
        try:
            if not self._character_service:
                from ephergent_generator.services.character_service import CharacterService
                self._character_service = CharacterService()
            
            # Check if characters are loaded
            characters = self._character_service.get_all_characters()
            character_count = len(characters) if characters else 0
            response_time = round((time.time() - start_time) * 1000, 2)
            
            healthy = character_count > 0
            
            return {
                "status": "healthy" if healthy else "no_data",
                "healthy": healthy,
                "response_time_ms": response_time,
                "details": {
                    "characters_loaded": character_count,
                    "characters": [char.get('id', char.get('name', 'Unknown')) for char in characters] if characters else []
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_image_service(self) -> Dict[str, Any]:
        """Check Image service status"""
        start_time = time.time()
        
        try:
            if not self._image_service:
                from ephergent_generator.services.image_service import ImageService
                self._image_service = ImageService()
            
            # Check service configuration
            status_info = self._image_service.get_service_status() if hasattr(self._image_service, 'get_service_status') else {}
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "healthy",
                "healthy": True,
                "response_time_ms": response_time,
                "details": status_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_comfyui_service(self) -> Dict[str, Any]:
        """Check ComfyUI service status"""
        start_time = time.time()
        
        try:
            if not self._comfyui_service:
                from ephergent_generator.services.comfyui_service import ComfyUIService
                self._comfyui_service = ComfyUIService()
            
            # Test connection to ComfyUI
            health_result = self._comfyui_service.test_connection()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "healthy" if health_result else "unhealthy",
                "healthy": health_result,
                "response_time_ms": response_time,
                "details": {
                    "url": getattr(self._comfyui_service, 'base_url', 'unknown'),
                    "enabled": getattr(self._comfyui_service, 'enabled', False)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_audio_service(self) -> Dict[str, Any]:
        """Check Audio/Kokoro TTS service status"""
        start_time = time.time()
        
        try:
            if not self._audio_service:
                from ephergent_generator.services.audio_service import AudioService
                self._audio_service = AudioService()
            
            # Check Kokoro TTS service availability
            status_info = {}
            
            # Try to get service status if method exists
            if hasattr(self._audio_service, 'test_kokoro_connection'):
                kokoro_available = self._audio_service.test_kokoro_connection()
                status_info['kokoro_available'] = kokoro_available
            else:
                status_info['kokoro_available'] = 'unknown'
            
            # Check voice configurations
            if hasattr(self._audio_service, 'voices'):
                status_info['voices_loaded'] = len(self._audio_service.voices)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            healthy = status_info.get('kokoro_available', False) if isinstance(status_info.get('kokoro_available'), bool) else True
            
            return {
                "status": "healthy" if healthy else "degraded",
                "healthy": healthy,
                "response_time_ms": response_time,
                "details": status_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_video_service(self) -> Dict[str, Any]:
        """Check Video service status"""
        start_time = time.time()
        
        try:
            if not self._video_service:
                from ephergent_generator.services.video_service import VideoService
                self._video_service = VideoService()
            
            # Check video service dependencies
            status_info = {}
            
            # Check if MoviePy is available
            if hasattr(self._video_service, 'MOVIEPY_AVAILABLE'):
                status_info['moviepy_available'] = self._video_service.MOVIEPY_AVAILABLE
            
            # Check asset directories
            if hasattr(self._video_service, 'assets_dir'):
                status_info['assets_dir_exists'] = self._video_service.assets_dir.exists()
            
            if hasattr(self._video_service, 'reporter_images_dir'):
                status_info['reporter_images_exist'] = self._video_service.reporter_images_dir.exists()
                if status_info['reporter_images_exist']:
                    reporter_images = list(self._video_service.reporter_images_dir.glob('*.png'))
                    status_info['reporter_image_count'] = len(reporter_images)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            healthy = status_info.get('moviepy_available', True)
            
            return {
                "status": "healthy" if healthy else "degraded",
                "healthy": healthy,
                "response_time_ms": response_time,
                "details": status_info
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_youtube_service(self) -> Dict[str, Any]:
        """Check YouTube service status"""
        start_time = time.time()
        
        try:
            if not self._youtube_service:
                from ephergent_generator.services.youtube_service import YouTubeService
                self._youtube_service = YouTubeService()
            
            # Check YouTube service configuration
            status_info = self._youtube_service.get_service_status() if hasattr(self._youtube_service, 'get_service_status') else {}
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Consider healthy if configured (can't test actual API without making requests)
            configured = status_info.get('configured', False)
            
            return {
                "status": "healthy" if configured else "misconfigured",
                "healthy": configured,
                "response_time_ms": response_time,
                "details": status_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def _check_ghost_service(self) -> Dict[str, Any]:
        """Check Ghost blog service status"""
        start_time = time.time()
        
        try:
            if not self._ghost_service:
                from ephergent_generator.services.ghost_service import GhostService
                self._ghost_service = GhostService()
            
            # Check Ghost service configuration and test JWT generation
            status_info = self._ghost_service.get_service_status()
            configured = self._ghost_service.is_configured()
            
            # Test JWT token generation if configured
            jwt_generation = False
            if configured:
                try:
                    token = self._ghost_service.get_jwt_token()
                    jwt_generation = len(token) > 100  # Valid JWT should be longer
                    status_info['jwt_token_length'] = len(token)
                except Exception as e:
                    status_info['jwt_error'] = str(e)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            healthy = configured and jwt_generation
            
            return {
                "status": "healthy" if healthy else "misconfigured",
                "healthy": healthy,
                "response_time_ms": response_time,
                "details": status_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Retrieve a lightweight status overview of the health monitoring system.

        This method provides a minimal snapshot of the monitoring system's state
        without performing comprehensive service checks.

        Returns:
            Dict[str, Any]: A minimal status dictionary containing:
                - timestamp: Current time in ISO format
                - system_status: Current monitoring system status
                - last_full_check: Timestamp of the most recent comprehensive health check
                - monitoring_enabled: Boolean indicating if monitoring is active

        Example:
            >>> health_service = HealthService()
            >>> quick_status = health_service.get_quick_status()
            >>> print(quick_status['system_status'])  # Typically prints "monitoring"
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "monitoring",
            "last_full_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "monitoring_enabled": True
        }