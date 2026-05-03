from ephergent_generator import create_app
from config import get_config
import os

def main():
    # Determine configuration environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_class = get_config(config_name)
    
    # Create app with configuration
    app = create_app(config_name)
    
    # Get configuration values
    host = app.config['FLASK_HOST']
    port = app.config['FLASK_PORT']
    debug = app.config['FLASK_DEBUG']
    
    print(f"🚀 Starting Season 03 Story Generator...")
    print(f"📝 Server running at http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"⚙️  Environment: {config_name}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Check for API key
    if app.config['GEMINI_API_KEY']:
        print("✅ Gemini API key configured")
    else:
        print("⚠️  Set GEMINI_API_KEY environment variable to enable story generation")
    
    # Show configuration warnings if any
    validation_errors = config_class.validate_required_config()
    if validation_errors:
        print("\n⚠️  Configuration warnings:")
        for error in validation_errors:
            print(f"   - {error}")
    
    print("")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
