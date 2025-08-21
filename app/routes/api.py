
from flask import Blueprint, request, jsonify, render_template
import json
import os
from datetime import datetime
from app.utils.scoring import calculate_score, classify_risk
from app.utils.offers import generate_loan_offers

api_bp = Blueprint('api', __name__)

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'rules', 'finance.json')
with open(RULES_PATH) as f:
    RULES = json.load(f)


@api_bp.route('/')
def api_docs():
    """API Documentation page"""
    return render_template('api_docs.html')


@api_bp.route('/docs')
def api_docs_alt():
    """Alternative route for API Documentation"""
    return render_template('api_docs.html')


@api_bp.route('/assess', methods=['POST'])
def api_assess():
    """
    REST API endpoint for risk assessment
    
    Expected JSON payload with required fields:
    - owner1_credit_score (number)
    - intelliscore (number) 
    - daily_average_balance (number)
    
    Returns JSON response with score, risk tier, and loan offers
    """
    try:
        # Check content type
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "status": "error"
            }), 400
        
        data = request.get_json()
        
        if not isinstance(data, dict):
            return jsonify({
                "error": "Request body must be a valid JSON object",
                "status": "error"
            }), 400

        # Get required fields based on ownership structure
        required_fields = []
        owner1_pct = float(data.get("owner1_ownership_pct", 100))
        
        for section_fields in RULES.values():
            for field_name in section_fields.keys():
                # Skip underwriter_adjustment (not required)
                if field_name == "underwriter_adjustment":
                    continue
                    
                # Skip owner2 fields if owner1 owns 50% or more
                if field_name.startswith("owner2_") and owner1_pct >= 50:
                    continue
                    
                required_fields.append(field_name)
        
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "error",
                "required_fields": required_fields
            }), 400

        # Validate numeric fields (only check fields that are actually required)
        non_numeric = []
        for field in required_fields:
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    non_numeric.append(field)
        
        if non_numeric:
            return jsonify({
                "error": f"Fields must be numeric: {', '.join(non_numeric)}",
                "status": "error"
            }), 400

        # Calculate score
        result = calculate_score(data, RULES)
        tier = classify_risk(result['total_score'])
        offers = generate_loan_offers(result['total_score'])

        # Log the assessment
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "api",
            "input": data,
            "score": result,
            "offers": offers,
            "tier": tier,
        }

        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Return response
        return jsonify({
            "status": "success",
            "assessment": {
                "score": result,
                "risk_tier": tier,
                "offers": offers
            },
            "input_data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@api_bp.route('/rules', methods=['GET'])
def api_rules():
    """
    Get the current scoring rules configuration
    """
    return jsonify({
        "status": "success",
        "rules": RULES,
        "timestamp": datetime.utcnow().isoformat()
    })


@api_bp.route('/health', methods=['GET'])
def api_health():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "service": "Qarari Risk Assessment API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })
