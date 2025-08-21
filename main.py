from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from app.routes.scorecard import scorecard_bp
from app.routes.underwriting_insights import insights_bp
from app.routes.admin import admin_bp
from app.routes.ml_training import ml_bp
from app.routes.train_model import train_bp
from app.routes.api import api_bp
from app.routes.user_management import user_bp
from app.security.rate_limiting import rate_limiter
from app.security.session import session_manager
from app.security.audit_log import audit_logger
import secrets
import os
import json

app = Flask(__name__)

# Secure session configuration
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; font-src 'self' cdn.jsdelivr.net"
    return response

# Rate limiting middleware
@app.before_request
def check_rate_limit():
    if request.endpoint and request.endpoint.startswith('api.'):
        if rate_limiter.is_rate_limited(request.remote_addr, 'api'):
            from app.security.audit_log import audit_logger
            audit_logger.log_security_violation('RATE_LIMIT_EXCEEDED', {
                'ip': request.remote_addr,
                'endpoint': request.endpoint
            })
            return {'error': 'Rate limit exceeded'}, 429

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


@app.route('/questionnaire')
def questionnaire():
    rules_path = os.path.join('app', 'rules', 'finance.json')
    with open(rules_path) as f:
        rules = json.load(f)
    return render_template('questionnaire.html', rules=rules)

@app.route('/builder')
def builder():
    """Risk Assessment Builder - allows dynamic question management"""
    rules_path = os.path.join('app', 'rules', 'finance.json')
    with open(rules_path) as f:
        rules = json.load(f)
    return render_template('builder.html', rules=rules)

@app.route('/builder/save', methods=['POST'])
def save_builder_rules():
    """Save updated rules from the builder"""
    try:
        rules_json = request.form.get('rules')
        if not rules_json:
            return "No rules data provided", 400

        rules = json.loads(rules_json)

        # Validate rules structure
        if not isinstance(rules, dict):
            return "Invalid rules format", 400

        # Save to file
        rules_path = os.path.join('app', 'rules', 'finance.json')
        with open(rules_path, 'w') as f:
            json.dump(rules, f, indent=2)

        return "Rules saved successfully", 200
    except Exception as e:
        return f"Error saving rules: {str(e)}", 500

@app.route('/builder/test', methods=['POST'])
def test_builder_scoring():
    """Test scoring with current rules"""
    try:
        test_data = request.get_json()
        if not test_data:
            return jsonify({"error": "No test data provided"}), 400

        # Load current rules
        rules_path = os.path.join('app', 'rules', 'finance.json')
        with open(rules_path) as f:
            rules = json.load(f)

        # Calculate score using the same logic as the main scoring
        from app.utils.scoring import calculate_finance_score
        from app.utils.offers import generate_offers

        score = calculate_finance_score(test_data, rules)

        # Determine tier
        total_score = score['total_score']
        if total_score >= 80:
            tier = 'low'
        elif total_score >= 60:
            tier = 'moderate'
        elif total_score >= 50:
            tier = 'high'
        else:
            tier = 'super_high'

        # Generate sample offers if score is good enough
        offers = []
        if tier in ['low', 'moderate']:
            offers = generate_offers(test_data, score, tier)

        return jsonify({
            "score": score,
            "tier": tier,
            "offers": offers
        })

    except Exception as e:
        return jsonify({"error": f"Error testing scoring: {str(e)}"}), 500


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