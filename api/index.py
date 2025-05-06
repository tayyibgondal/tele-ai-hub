import sys
import os

# Add the src directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Import the Flask app
    from src.app import app
    
    # For local testing
    if __name__ == "__main__":
        app.run()
    
    # This is the handler Vercel uses
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
except Exception as e:
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify(error=f"Import error: {str(e)}", path=path, python_path=sys.path) 