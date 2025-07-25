from flask import Flask
from app.routes.scorecard import scorecard_bp

app = Flask(__name__)
app.secret_key = 'supersecret'

# Register Blueprints
app.register_blueprint(scorecard_bp)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
