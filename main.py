from flask import Flask, render_template, request
from app.routes.scorecard import scorecard_bp
from app.routes.underwriting_insights import insights_bp

app = Flask(__name__)
app.secret_key = "supersecret"

# Register Blueprints
app.register_blueprint(scorecard_bp, url_prefix='/score')
app.register_blueprint(insights_bp, url_prefix='/insights')


@app.route('/')
def home():
    return render_template('form.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
