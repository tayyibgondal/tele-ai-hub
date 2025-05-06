from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    return jsonify({
        "status": "success",
        "message": "Flask app is running on Vercel!",
        "path": path
    })

# Vercel requires a handler function
def handler(request, context):
    """Handle request as a WSGI application"""
    return app(request['body'], request['headers'])

# For local testing
if __name__ == '__main__':
    app.run(debug=True) 