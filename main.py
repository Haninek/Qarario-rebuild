from flask import Flask, render_template, request, redirect, url_for
from app.routes.scorecard import scorecard_bp
from app.routes.underwriting_insights import insights_bp

app = Flask(__name__)
app.secret_key = "supersecret"

# Register Blueprints
app.register_blueprint(scorecard_bp, url_prefix='/score')
app.register_blueprint(insights_bp, url_prefix='/insights')


@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/builder')
def builder():
    import os
    path = os.path.join(os.path.dirname(__file__), 'app', 'rules', 'finance.json')
    with open(path, 'r') as f:
        current_rules = f.read()
    return render_template('builder.html', rules=current_rules)

@app.route('/builder/save', methods=['POST'])
def save_builder():
    import os, json
    data = json.loads(request.form.get("rules", "{}"))
    path = os.path.join(os.path.dirname(__file__), 'app', 'rules', 'finance.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return redirect(url_for('builder'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
