"""
Safety1st Crash Risk Calculator API
Main Flask application entry point
"""

from flask import Flask, jsonify
from flask_cors import CORS
from api.routes import api_blueprint
from config.settings import Config


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend communication
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Register API blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "service": "Safety1st Crash Risk Calculator API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/api/health",
                "evaluate": "/api/evaluate-crash (MAIN - AI-enhanced)",
                "calculate": "/api/crash-risk/calculate (baseline only)",
                "analyze": "/api/crash-risk/analyze (same as evaluate)",
                "test": "/api/test/example-crash"
            }
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": "Endpoint not found",
            "message": "The requested URL was not found on the server."
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred."
        }), 500

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Method not allowed",
            "message": "The method is not allowed for the requested URL."
        }), 405

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 70)
    print("Safety1st Crash Risk Calculator API Starting...")
    print("=" * 70)
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"\nAPI Endpoints:")
    print(f"  - Health Check:       http://localhost:5000/api/health")
    print(f"  - Evaluate (MAIN):    http://localhost:5000/api/evaluate-crash")
    print(f"  - Calculate (basic):  http://localhost:5000/api/crash-risk/calculate")
    print(f"  - Analyze (alias):    http://localhost:5000/api/crash-risk/analyze")
    print(f"  - Test Example:       http://localhost:5000/api/test/example-crash")
    print(f"\nArchitecture: Baseline Physics + Web Scraper + Gemini AI")
    print("=" * 70)

    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )
