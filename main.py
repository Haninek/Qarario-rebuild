
from flask import Flask, render_template
from app.routes.scorecard import scorecard_bp
from app.routes.underwriting_insights import insights_bp
from app.routes.admin import admin_bp
from app.routes.ml_training import ml_bp
from app.routes.train_model import train_bp

app = Flask(__name__)
app.secret_key = "supersecret"

# Register Blueprints
app.register_blueprint(scorecard_bp, url_prefix='/score')
app.register_blueprint(insights_bp, url_prefix='/insights')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(ml_bp, url_prefix='/ml')
app.register_blueprint(train_bp, url_prefix='/train')

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
