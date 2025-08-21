from flask import Flask, render_template, request, redirect, url_for
from app.routes.scorecard import scorecard_bp
from app.routes.underwriting_insights import insights_bp
from app.routes.admin import admin_bp
from app.routes.ml_training import ml_bp
from app.routes.train_model import train_bp
from app.routes.api import api_bp
from app.routes.user_management import user_bp

app = Flask(__name__)
app.secret_key = "supersecret"

# Register Blueprints
app.register_blueprint(scorecard_bp, url_prefix='/score')
app.register_blueprint(insights_bp, url_prefix='/insights')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(ml_bp, url_prefix='/ml')
app.register_blueprint(train_bp, url_prefix='/train')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/user')


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

@app.route('/builder/test', methods=['POST'])
def test_builder_scoring():
    from app.utils.scoring import calculate_score, classify_risk
    import os, json
    
    # Load current rules
    path = os.path.join(os.path.dirname(__file__), 'app', 'rules', 'finance.json')
    with open(path, 'r') as f:
        rules = json.load(f)
    
    # Get test data
    test_data = request.get_json()
    
    # Calculate score using current logic
    result = calculate_score(test_data, rules)
    tier = classify_risk(result['total_score'])
    
    return jsonify({
        "score": result,
        "tier": tier,
        "input_data": test_data
    })


@app.route('/admin')
def admin_dashboard():
    import os, json
    log_path = os.path.join(os.path.dirname(__file__), 'logs', 'underwriting_data.jsonl')
    try:
        with open(log_path, 'r') as f:
            logs = [json.loads(line.strip()) for line in f.readlines()][-10:]  # Last 10
    except:
        logs = []
    return render_template('admin.html', logs=logs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
