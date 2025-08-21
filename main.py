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
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Add custom Jinja2 filter for JSON conversion
@app.template_filter('tojsonfilter')
def to_json_filter(obj):
    return json.dumps(obj)

def analyze_historical_patterns(logs_path):
    """Analyze historical underwriting data to identify patterns"""
    patterns = {
        'high_risk_indicators': [],
        'low_risk_indicators': [],
        'missing_data_points': [],
        'score_correlations': {}
    }
    
    try:
        if not os.path.exists(logs_path):
            return patterns
            
        with open(logs_path, 'r') as f:
            entries = []
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except:
                        continue
        
        if not entries:
            return patterns
            
        # Analyze score distributions and field correlations
        high_scores = [e for e in entries if e.get('score', {}).get('total_score', 0) >= 70]
        low_scores = [e for e in entries if e.get('score', {}).get('total_score', 0) < 50]
        
        # Find common characteristics in high/low performing applications
        if high_scores:
            patterns['low_risk_indicators'] = extract_common_patterns(high_scores)
        if low_scores:
            patterns['high_risk_indicators'] = extract_common_patterns(low_scores)
            
        # Identify frequently missing data points
        all_fields = set()
        for entry in entries:
            all_fields.update(entry.get('input', {}).keys())
        
        missing_counts = {}
        for field in all_fields:
            missing_count = sum(1 for e in entries if not e.get('input', {}).get(field))
            if missing_count > len(entries) * 0.3:  # Missing in >30% of applications
                missing_counts[field] = missing_count
                
        patterns['missing_data_points'] = list(missing_counts.keys())
        
    except Exception:
        pass
        
    return patterns

def extract_common_patterns(entries):
    """Extract common patterns from a set of entries"""
    patterns = []
    if not entries:
        return patterns
        
    # Sample analysis - in production, this would be more sophisticated
    common_fields = {}
    for entry in entries:
        input_data = entry.get('input', {})
        for field, value in input_data.items():
            if field not in common_fields:
                common_fields[field] = []
            common_fields[field].append(value)
    
    # Find fields with consistent values/ranges
    for field, values in common_fields.items():
        if len(set(str(v) for v in values)) <= 3:  # Limited variety
            patterns.append(f"{field}: {list(set(str(v) for v in values))}")
    
    return patterns[:5]  # Top 5 patterns

def get_current_market_insights():
    """Get current market trends and insights that should influence risk assessment"""
    # In production, this would connect to real market data APIs
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    insights = {
        'economic_climate': determine_economic_climate(),
        'industry_trends': get_industry_trends(),
        'regulatory_changes': get_regulatory_updates(),
        'seasonal_factors': get_seasonal_considerations(current_month),
        'recommended_focus_areas': []
    }
    
    # Determine focus areas based on current trends
    if insights['economic_climate'] == 'uncertain':
        insights['recommended_focus_areas'].extend([
            'Cash flow stability',
            'Industry resilience',
            'Emergency reserves'
        ])
    
    if current_month in [11, 12, 1, 2]:  # Q4/Q1
        insights['recommended_focus_areas'].append('Seasonal revenue fluctuations')
    
    return insights

def determine_economic_climate():
    """Determine current economic climate (simplified simulation)"""
    # In production, this would analyze real economic indicators
    climates = ['stable', 'growth', 'uncertain', 'declining']
    return random.choice(climates)  # Simplified for demo

def get_industry_trends():
    """Get current industry-specific trends"""
    return {
        'tech': 'Strong growth but higher volatility',
        'retail': 'E-commerce shift continues',
        'hospitality': 'Recovery phase post-pandemic',
        'healthcare': 'Stable with regulatory changes',
        'manufacturing': 'Supply chain optimization focus'
    }

def get_regulatory_updates():
    """Get recent regulatory changes affecting underwriting"""
    return [
        'Updated data privacy requirements',
        'Enhanced AML compliance standards',
        'New small business lending guidelines'
    ]

def get_seasonal_considerations(month):
    """Get seasonal factors that might affect risk assessment"""
    seasonal_map = {
        1: 'Post-holiday cash flow impact',
        2: 'Tax season preparation',
        3: 'Q1 performance assessment',
        4: 'Spring business cycle start',
        5: 'Mid-year planning',
        6: 'Q2 performance review',
        7: 'Summer seasonal effects',
        8: 'Back-to-school impact',
        9: 'Q3 closing preparations',
        10: 'Year-end planning begins',
        11: 'Holiday season preparation',
        12: 'Year-end financial close'
    }
    return seasonal_map.get(month, 'General business cycle considerations')

def generate_smart_questions(category, existing_questions, historical_insights):
    """Generate AI-powered question suggestions based on data and trends"""
    
    question_bank = {
        'Personal Credit Information': {
            'credit_analysis': [
                {
                    'text': 'Credit score trend over last 24 months',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Credit trends predict future payment behavior better than point-in-time scores'
                },
                {
                    'text': 'Debt-to-income ratio (personal)',
                    'weight': 9,
                    'scoring': 'lower_better',
                    'rationale': 'High DTI ratios strongly correlate with business loan defaults'
                },
                {
                    'text': 'Number of open credit lines',
                    'weight': 6,
                    'scoring': 'threshold_based',
                    'rationale': 'Too few or too many credit lines indicate risk'
                }
            ]
        },
        'Business Information': {
            'operational_metrics': [
                {
                    'text': 'Business license expiration date',
                    'weight': 7,
                    'scoring': 'threshold_based',
                    'rationale': 'Expired licenses indicate compliance issues'
                },
                {
                    'text': 'Industry certification status',
                    'weight': 6,
                    'scoring': 'categorical',
                    'rationale': 'Professional certifications reduce operational risk'
                },
                {
                    'text': 'Employee count stability (last 12 months)',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Stable workforce indicates business sustainability'
                }
            ]
        },
        'Bank Analysis': {
            'cash_flow': [
                {
                    'text': 'Seasonal cash flow variance percentage',
                    'weight': 8,
                    'scoring': 'lower_better',
                    'rationale': 'High seasonal variance increases repayment risk'
                },
                {
                    'text': 'Average time to clear deposited checks',
                    'weight': 5,
                    'scoring': 'lower_better',
                    'rationale': 'Longer clearing times may indicate customer quality issues'
                },
                {
                    'text': 'Electronic vs cash transaction ratio',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Higher electronic ratios indicate modern business practices'
                }
            ]
        },
        'Background & Verification': {
            'compliance': [
                {
                    'text': 'Tax lien status and resolution date',
                    'weight': 9,
                    'scoring': 'categorical',
                    'rationale': 'Unresolved tax issues are critical risk factors'
                },
                {
                    'text': 'Professional liability insurance amount',
                    'weight': 7,
                    'scoring': 'higher_better',
                    'rationale': 'Adequate insurance coverage reduces lender risk exposure'
                },
                {
                    'text': 'Better Business Bureau rating',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Customer complaints correlate with business stability'
                }
            ]
        },
        'Online Presence & Digital Footprint': {
            'digital_maturity': [
                {
                    'text': 'Online review response rate',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Active review management indicates customer focus'
                },
                {
                    'text': 'Social media engagement rate',
                    'weight': 5,
                    'scoring': 'higher_better',
                    'rationale': 'Strong online engagement indicates market presence'
                },
                {
                    'text': 'E-commerce platform integration',
                    'weight': 7,
                    'scoring': 'categorical',
                    'rationale': 'Digital sales channels provide revenue resilience'
                }
            ]
        },
        'Collateral & Assets': {
            'asset_verification': [
                {
                    'text': 'Asset appraisal date and validity',
                    'weight': 8,
                    'scoring': 'threshold_based',
                    'rationale': 'Recent appraisals ensure accurate collateral values'
                },
                {
                    'text': 'Equipment maintenance schedule compliance',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Well-maintained assets retain higher value'
                },
                {
                    'text': 'Real estate appreciation/depreciation trend',
                    'weight': 7,
                    'scoring': 'higher_better',
                    'rationale': 'Asset value trends affect collateral adequacy'
                }
            ]
        },
        'Market Conditions': {
            'market_analysis': [
                {
                    'text': 'Local market share percentage',
                    'weight': 7,
                    'scoring': 'higher_better',
                    'rationale': 'Market dominance provides competitive advantage'
                },
                {
                    'text': 'Industry growth rate in operating region',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Growing markets support business expansion'
                },
                {
                    'text': 'Economic diversification index of operating area',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Diversified economies are more resilient to shocks'
                }
            ]
        },
        'financial': {
            'cash_flow': [
                {
                    'text': 'Average daily cash position over last 90 days',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Recent cash flow patterns are stronger predictors than historical averages'
                },
                {
                    'text': 'Days with negative cash balance in last 6 months',
                    'weight': 7,
                    'scoring': 'lower_better',
                    'rationale': 'Frequency of cash shortfalls indicates operational stability'
                },
                {
                    'text': 'Largest single-day cash outflow in last 90 days',
                    'weight': 6,
                    'scoring': 'threshold_based',
                    'rationale': 'Large irregular expenses may indicate hidden liabilities'
                }
            ],
            'revenue': [
                {
                    'text': 'Revenue concentration: % from top 3 customers',
                    'weight': 9,
                    'scoring': 'lower_better',
                    'rationale': 'Customer concentration risk is critical in uncertain markets'
                },
                {
                    'text': 'Monthly recurring revenue percentage',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Predictable revenue streams reduce default risk significantly'
                },
                {
                    'text': 'Revenue growth rate (last 12 months)',
                    'weight': 7,
                    'scoring': 'threshold_based',
                    'rationale': 'Sustainable growth indicates market viability'
                }
            ]
        },
        'operational': {
            'technology': [
                {
                    'text': 'Digital payment processing percentage',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Digital-native businesses show better resilience'
                },
                {
                    'text': 'Cloud infrastructure adoption level',
                    'weight': 5,
                    'scoring': 'categorical',
                    'rationale': 'Cloud adoption indicates operational efficiency and scalability'
                },
                {
                    'text': 'Cybersecurity insurance coverage amount',
                    'weight': 7,
                    'scoring': 'threshold_based',
                    'rationale': 'Cyber risks are increasing; coverage indicates risk awareness'
                }
            ],
            'supply_chain': [
                {
                    'text': 'Number of critical suppliers (>20% of inputs)',
                    'weight': 8,
                    'scoring': 'lower_better',
                    'rationale': 'Supply chain concentration risk has increased post-COVID'
                },
                {
                    'text': 'Inventory turnover ratio (last 12 months)',
                    'weight': 7,
                    'scoring': 'threshold_based',
                    'rationale': 'Efficient inventory management indicates operational maturity'
                },
                {
                    'text': 'Local supplier percentage',
                    'weight': 6,
                    'scoring': 'higher_better',
                    'rationale': 'Local sourcing reduces supply chain disruption risk'
                }
            ]
        },
        'market': {
            'competition': [
                {
                    'text': 'Market share in primary geographic area',
                    'weight': 7,
                    'scoring': 'higher_better',
                    'rationale': 'Local market position indicates competitive moat strength'
                },
                {
                    'text': 'Price flexibility: % margin if forced to cut prices 10%',
                    'weight': 8,
                    'scoring': 'higher_better',
                    'rationale': 'Pricing power is crucial during economic uncertainty'
                },
                {
                    'text': 'New competitor entries in last 24 months',
                    'weight': 6,
                    'scoring': 'lower_better',
                    'rationale': 'Market saturation affects long-term viability'
                }
            ]
        }
    }
    
    # Select questions based on category and current trends
    suggested_questions = []
    
    if category in question_bank:
        for subcategory, questions in question_bank[category].items():
            # Add market-relevant questions
            for question in questions:
                if not any(q['text'].lower() in question['text'].lower() for q in existing_questions):
                    # Enhance with AI insights
                    enhanced_question = enhance_question_with_ai(question, historical_insights)
                    suggested_questions.append(enhanced_question)
    
    # Add trend-based questions
    trend_questions = generate_trend_based_questions()
    for question in trend_questions:
        if not any(q['text'].lower() in question['text'].lower() for q in existing_questions):
            suggested_questions.append(question)
    
    # Sort by relevance score
    suggested_questions.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return suggested_questions[:10]  # Return top 10 suggestions

def enhance_question_with_ai(question, historical_insights):
    """Enhance a question with AI-driven insights"""
    enhanced = question.copy()
    
    # Add relevance score based on historical patterns
    relevance_score = 5  # Base score
    
    # Increase relevance if related to historical high-risk indicators
    for indicator in historical_insights.get('high_risk_indicators', []):
        if any(word in indicator.lower() for word in question['text'].lower().split()):
            relevance_score += 2
    
    # Increase relevance if addressing missing data points
    for missing_field in historical_insights.get('missing_data_points', []):
        if missing_field.lower() in question['text'].lower():
            relevance_score += 3
            enhanced['rationale'] += f" [Missing in {len(historical_insights.get('missing_data_points', []))} recent applications]"
    
    enhanced['relevance_score'] = relevance_score
    enhanced['ai_enhanced'] = True
    
    return enhanced

def generate_trend_based_questions():
    """Generate questions based on current market trends"""
    current_trends = get_current_market_insights()
    trend_questions = []
    
    # Economic climate-based questions
    if current_trends['economic_climate'] == 'uncertain':
        trend_questions.extend([
            {
                'text': 'Stress test: Months of operation with 30% revenue drop',
                'weight': 9,
                'scoring': 'higher_better',
                'rationale': 'Economic uncertainty requires stronger resilience measures',
                'relevance_score': 9,
                'trend_based': True
            },
            {
                'text': 'Emergency fund as % of monthly operating expenses',
                'weight': 8,
                'scoring': 'higher_better',
                'rationale': 'Cash reserves are critical during market uncertainty',
                'relevance_score': 8,
                'trend_based': True
            }
        ])
    
    # Seasonal considerations
    current_month = datetime.now().month
    if current_month in [11, 12]:  # Holiday season
        trend_questions.append({
            'text': 'Holiday season revenue as % of annual total',
            'weight': 7,
            'scoring': 'threshold_based',
            'rationale': 'Seasonal dependency affects cash flow predictability',
            'relevance_score': 7,
            'trend_based': True
        })
    
    return trend_questions

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
    try:
        rules_path = os.path.join('app', 'rules', 'finance.json')
        with open(rules_path, 'r') as f:
            rules = json.load(f)
        
        # Debug: Print rules structure to console
        print(f"Loaded rules with {len(rules)} sections")
        for section, fields in rules.items():
            print(f"  Section '{section}': {len(fields)} fields")
            
        return render_template('builder.html', rules=rules)
    except Exception as e:
        print(f"Error loading builder: {e}")
        # Return with empty rules if file doesn't exist or is corrupted
        return render_template('builder.html', rules={})

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

@app.route('/builder/ai-suggestions', methods=['POST'])
def get_ai_question_suggestions():
    """Get AI-generated question suggestions based on current trends and historical data"""
    try:
        request_data = request.get_json() or {}
        category = request_data.get('category', 'general')
        existing_questions = request_data.get('existing_questions', [])
        
        # Analyze historical data from logs
        logs_path = os.path.join('logs', 'underwriting_data.jsonl')
        historical_insights = analyze_historical_patterns(logs_path)
        
        # Generate AI suggestions based on current market trends and data patterns
        suggestions = generate_smart_questions(category, existing_questions, historical_insights)
        
        return jsonify({
            "suggestions": suggestions,
            "market_insights": get_current_market_insights(),
            "data_patterns": historical_insights
        })
        
    except Exception as e:
        return jsonify({"error": f"Error generating AI suggestions: {str(e)}"}), 500


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