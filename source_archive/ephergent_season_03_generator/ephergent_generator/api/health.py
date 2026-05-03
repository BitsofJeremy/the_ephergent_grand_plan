"""Health check API endpoints for monitoring and orchestration.

Provides comprehensive health checking capabilities including:
- Liveness probes (is the application running?)
- Readiness probes (is the application ready to serve traffic?)
- Full health checks (detailed service-by-service status)

These endpoints are designed for use by monitoring systems, load balancers,
and container orchestration platforms like Kubernetes.
"""

from flask import current_app, jsonify
from flask_restx import Namespace, Resource, fields
from ephergent_generator.services.health_service import HealthService
from ephergent_generator.utils.metrics import metrics_service

# Create health service instance
health_service_instance = HealthService()

# Create a health namespace
ns = Namespace('health', description='Service health checks and monitoring')

# Health Check Models
service_health_model = ns.model('ServiceHealth', {
    'status': fields.String(description='Service status (healthy/unhealthy/degraded/error)'),
    'healthy': fields.Boolean(description='Whether service is healthy'),
    'response_time_ms': fields.Float(description='Response time in milliseconds'),
    'details': fields.Raw(description='Additional service details'),
    'error': fields.String(description='Error message if service check failed')
})

overall_health_model = ns.model('OverallHealth', {
    'timestamp': fields.String(description='ISO timestamp of health check'),
    'overall_status': fields.String(description='Overall system status (healthy/degraded/unhealthy)'),
    'services': fields.Raw(description='Dictionary of service health statuses'),
    'summary': fields.Raw(description='Summary statistics'),
    'check_duration_ms': fields.Float(description='Total health check duration')
})

liveness_model = ns.model('Liveness', {
    'status': fields.String(description='Liveness status'),
    'timestamp': fields.String(description='ISO timestamp')
})

readiness_model = ns.model('Readiness', {
    'status': fields.String(description='Readiness status'),
    'ready': fields.Boolean(description='Whether application is ready'),
    'checks': fields.Raw(description='Critical service checks'),
    'timestamp': fields.String(description='ISO timestamp')
})


@ns.route('/liveness')
class LivenessProbe(Resource):
    """Liveness probe endpoint.

    Kubernetes uses liveness probes to know when to restart a container.
    This endpoint checks if the application process is running and responsive.
    It should return 200 OK as long as the process is alive, even if dependencies are down.
    """

    @ns.doc('liveness_probe')
    @ns.marshal_with(liveness_model)
    def get(self):
        """Check if application is alive (process is running).

        Returns:
            200 OK: Application process is alive
            500 Error: Application process is not responsive

        Note:
            This is a minimal check that only verifies the Flask app is running.
            It does NOT check dependencies - those are checked in readiness probe.
        """
        try:
            # Record metric
            metrics_service.external_service_available.labels(service='application').set(1)

            # Get quick status (minimal overhead)
            status = health_service_instance.get_quick_status()

            return {
                'status': 'alive',
                'timestamp': status['timestamp']
            }, 200

        except Exception as e:
            current_app.logger.error(f"Liveness probe failed: {str(e)}")
            metrics_service.external_service_available.labels(service='application').set(0)

            return {
                'status': 'error',
                'error': str(e)
            }, 500


@ns.route('/readiness')
class ReadinessProbe(Resource):
    """Readiness probe endpoint.

    Kubernetes uses readiness probes to know when a container is ready to start accepting traffic.
    This endpoint checks if the application and its critical dependencies are ready.
    """

    @ns.doc('readiness_probe')
    @ns.marshal_with(readiness_model)
    def get(self):
        """Check if application is ready to serve traffic.

        Checks critical dependencies:
        - Database connectivity
        - Core services availability

        Returns:
            200 OK: Application is ready to serve traffic
            503 Service Unavailable: Application is not ready (dependencies down)
        """
        try:
            # Get full health status
            full_status = health_service_instance.get_all_service_status()

            # Check critical services for readiness
            critical_services = ['database', 'gemini', 'character']
            critical_checks = {}
            all_critical_healthy = True

            for service_name in critical_services:
                service_status = full_status['services'].get(service_name, {})
                is_healthy = service_status.get('healthy', False)
                critical_checks[service_name] = {
                    'healthy': is_healthy,
                    'status': service_status.get('status', 'unknown')
                }

                if not is_healthy:
                    all_critical_healthy = False

            # Update metrics
            for service_name, check_result in critical_checks.items():
                metrics_service.set_service_availability(
                    service_name,
                    check_result['healthy']
                )

            if all_critical_healthy:
                return {
                    'status': 'ready',
                    'ready': True,
                    'checks': critical_checks,
                    'timestamp': full_status['timestamp']
                }, 200
            else:
                return {
                    'status': 'not_ready',
                    'ready': False,
                    'checks': critical_checks,
                    'timestamp': full_status['timestamp']
                }, 503

        except Exception as e:
            current_app.logger.error(f"Readiness probe failed: {str(e)}")
            return {
                'status': 'error',
                'ready': False,
                'error': str(e)
            }, 503


@ns.route('/full')
@ns.route('/')  # Also respond at /api/health
class FullHealthCheck(Resource):
    """Comprehensive health check endpoint.

    Provides detailed health information for all services and dependencies.
    Use this for monitoring dashboards and detailed troubleshooting.
    """

    @ns.doc('full_health_check')
    @ns.marshal_with(overall_health_model)
    def get(self):
        """Get comprehensive health status for all services.

        Returns detailed health information including:
        - Overall system status
        - Individual service statuses
        - Response times
        - Service details and configurations
        - Summary statistics

        Returns:
            200 OK: Health check completed (status may be degraded or unhealthy)

        Note:
            This endpoint always returns 200 OK even if services are unhealthy.
            Check the 'overall_status' field for actual health status.
        """
        try:
            # Perform comprehensive health check
            health_status = health_service_instance.get_all_service_status()

            # Update Prometheus metrics for each service
            for service_name, service_data in health_status['services'].items():
                is_healthy = service_data.get('healthy', False)
                metrics_service.set_service_availability(service_name, is_healthy)

            current_app.logger.info(
                f"Full health check completed: {health_status['overall_status']}",
                extra={
                    'healthy_services': health_status['summary']['healthy_services'],
                    'unhealthy_services': health_status['summary']['unhealthy_services'],
                    'check_duration_ms': health_status['check_duration_ms']
                }
            )

            return health_status, 200

        except Exception as e:
            current_app.logger.error(f"Full health check failed: {str(e)}")
            ns.abort(500, message=f"Health check error: {str(e)}")


@ns.route('/quick')
class QuickHealthCheck(Resource):
    """Quick health check endpoint with minimal overhead."""

    @ns.doc('quick_health_check')
    def get(self):
        """Get quick health status without performing service checks.

        Returns:
            200 OK: Quick status retrieved successfully

        Note:
            This is a lightweight endpoint that doesn't perform actual service checks.
            Use /health/full for comprehensive status.
        """
        try:
            status = health_service_instance.get_quick_status()
            return status, 200

        except Exception as e:
            current_app.logger.error(f"Quick health check failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }, 500
