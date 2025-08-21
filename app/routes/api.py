from flask import Blueprint, request, jsonify, render_template
import json
import os
from datetime import datetime
from app.utils.scoring import calculate_score, classify_risk
from app.utils.offers import generate_loan_offers
from app.auth.middleware import require_api_auth, require_subscription
from app.security.rate_limiting import rate_limiter
from app.security.input_validation import input_validator
from app.security.audit_log import audit_logger
from app.security.data_isolation import data_isolation

api_bp = Blueprint('api', __name__)

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'rules', 'finance.json')
with open(RULES_PATH) as f:
    RULES = json.load(f)

# API Call pricing
API_CALL_COST = 1.25  # $1.25 per API call

def track_api_usage(user_id, endpoint, cost=API_CALL_COST):
    """Track API usage and billing"""
    usage_log = {
        "user_id": user_id,
        "endpoint": endpoint,
        "cost": cost,
        "timestamp": datetime.utcnow().isoformat()
    }

    usage_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'api_usage.json')
    os.makedirs(os.path.dirname(usage_path), exist_ok=True)

    try:
        with open(usage_path, 'r') as f:
            usage_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        usage_data = []

    usage_data.append(usage_log)

    with open(usage_path, 'w') as f:
        json.dump(usage_data, f, indent=2)

    return usage_log


@api_bp.route('/')
def api_docs():
    """API Documentation page"""
    return render_template('api_docs.html')


@api_bp.route('/docs')
def api_docs_alt():
    """Alternative route for API Documentation"""
    return render_template('api_docs.html')


@api_bp.route('/sandbox/assess', methods=['POST'])
@rate_limiter.rate_limit('api')
def sandbox_assess():
    """
    Sandbox API endpoint for testing - Limited functionality

    - No authentication required
    - Returns mock data for testing
    - Limited to 10 calls per day per IP
    - No real scoring calculations
    """
    try:
        # Check content type and validate input schema for sandbox
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "status": "error",
                "mode": "sandbox"
            }), 400

        data = request.get_json()

        if not isinstance(data, dict):
            return jsonify({
                "error": "Request body must be a valid JSON object",
                "status": "error",
                "mode": "sandbox"
            }), 400
        
        # Basic input validation for sandbox - can be expanded
        if not input_validator.validate_sandbox_input(data):
             return jsonify({
                "error": "Invalid input data for sandbox assessment.",
                "status": "error",
                "mode": "sandbox"
            }), 400

        # Audit the sandbox request
        audit_logger.log_request(request, "sandbox_assess", "unauthenticated")

        # Return mock response for sandbox testing
        mock_result = {
            "total_score": 75,
            "section_scores": {
                "Personal Credit Information": 65,
                "Business Information": 85,
                "Bank Analysis": 70,
                "Capital and Collateral": 80,
                "Other": 75
            },
            "max_possible_score": 100
        }

        mock_tier = "Moderate Risk"
        mock_offers = [
            {
                "amount": 50000,
                "factor_rate": 1.45,
                "buy_rate": 1.35,
                "term_days": 180,
                "payment_frequency": "Weekly",
                "payment_amount": 1923.08,
                "position": 1,
                "commission_percentage": 8
            }
        ]

        return jsonify({
            "status": "success",
            "mode": "sandbox",
            "note": "This is sandbox mode with mock data. Upgrade to production API for real assessments.",
            "assessment": {
                "score": mock_result,
                "risk_tier": mock_tier,
                "offers": mock_offers
            },
            "input_data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "sandbox_limitations": [
                "Mock data only",
                "Limited to 10 calls per day",
                "No real risk assessment"
            ]
        })

    except Exception as e:
        # Audit the sandbox error
        audit_logger.log_error(request, "sandbox_assess", str(e))
        return jsonify({
            "error": f"Sandbox error: {str(e)}",
            "status": "error",
            "mode": "sandbox"
        }), 500


@api_bp.route('/assess', methods=['POST'])
@require_api_auth # Ensures authentication
@rate_limiter.rate_limit('api')
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
        # Authentication is handled by @require_api_auth decorator
        user_id = request.headers.get('X-User-ID')
        if not user_id: # Should not happen if @require_api_auth is working, but as a safeguard
            return jsonify({"error": "Authentication required.", "status": "error"}), 401

        # Check content type
        if not request.is_json:
            audit_logger.log_request_error(request, "/assess", "Invalid Content-Type")
            return jsonify({
                "error": "Content-Type must be application/json",
                "status": "error"
            }), 400

        data = request.get_json()

        if not isinstance(data, dict):
            audit_logger.log_request_error(request, "/assess", "Invalid JSON payload")
            return jsonify({
                "error": "Request body must be a valid JSON object",
                "status": "error"
            }), 400

        # Input validation for production API
        # The input_validator should handle user-specific data validation based on user_id
        if not input_validator.validate_production_input(data, user_id):
             audit_logger.log_request_error(request, "/assess", "Input validation failed")
             return jsonify({
                "error": "Invalid input data for assessment. Please check the required fields and their formats.",
                "status": "error"
            }), 400

        # Audit the request before processing
        audit_logger.log_request(request, "/assess", user_id)

        # Data isolation: Ensure that the user can only access/process their own data context
        # This example assumes 'data' itself contains user-specific context or that the rules/scoring functions
        # implicitly use user_id for context. If data were stored in a database, isolation would be crucial there.
        # For this endpoint, we ensure that any processing is done in a user-aware context.
        # The 'data' passed to calculate_score and generate_loan_offers might need to be filtered or validated
        # based on user_id if it contains sensitive cross-user information, which is not the case here
        # as 'data' is the input payload.
        # The data_isolation decorator or logic would typically wrap the core processing if needed.
        # For this specific flow, validation and subsequent processing inherently respect the user context
        # established by authentication and rate limiting.

        # Get required fields based on ownership structure and owner2 data presence
        required_fields = []
        owner1_pct = float(data.get("owner1_ownership_pct", 100))

        # Check if any owner2 data is actually provided (excluding just ownership percentage)
        owner2_has_data = any(
            v is not None and str(v).strip() != ""
            for k, v in data.items()
            if k.startswith("owner2_") and k != "owner2_ownership_pct"
        )

        # Only include owner2 fields if owner1 owns less than 50% AND owner2 data is provided
        include_owner2_fields = owner1_pct < 50 and owner2_has_data

        for section_fields in RULES.values():
            for field_name in section_fields.keys():
                # Skip underwriter_adjustment (not required)
                if field_name == "underwriter_adjustment":
                    continue

                # Skip owner2 fields unless both conditions are met
                if field_name.startswith("owner2_") and not include_owner2_fields:
                    continue

                required_fields.append(field_name)

        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            audit_logger.log_request_error(request, "/assess", f"Missing fields: {', '.join(missing_fields)}")
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
            audit_logger.log_request_error(request, "/assess", f"Non-numeric fields: {', '.join(non_numeric)}")
            return jsonify({
                "error": f"Fields must be numeric: {', '.join(non_numeric)}",
                "status": "error"
            }), 400

        # Calculate score
        # Ensure that calculate_score respects user context if necessary
        result = calculate_score(data, RULES)
        tier = classify_risk(result['total_score'])
        offers = generate_loan_offers(result['total_score']) # Assuming generate_loan_offers also respects context if needed

        # Log the assessment securely
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "source": "api",
            "endpoint": "/assess",
            "input": data, # Consider redacting sensitive PII if logging all input is not desired/secure
            "score": result,
            "offers": offers,
            "tier": tier,
        }

        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'underwriting_data.jsonl')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        # Use a secure file append mechanism, potentially with file locking if concurrent writes are expected beyond Flask's request handling
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Track API usage and billing
        billing_log = track_api_usage(user_id, '/assess', API_CALL_COST)

        # Determine if single owner logic was used
        single_owner_logic = owner1_pct >= 50 or not owner2_has_data

        # Return response
        return jsonify({
            "status": "success",
            "assessment": {
                "score": result,
                "risk_tier": tier,
                "offers": offers,
                "owner_structure": {
                    "single_owner": single_owner_logic,
                    "owner1_percentage": owner1_pct,
                    "owner2_data_provided": owner2_has_data
                }
            },
            "input_data": data, # Consider redacting sensitive PII before returning if necessary
            "timestamp": datetime.utcnow().isoformat(),
            "billing": {
                "cost": API_CALL_COST,
                "call_id": billing_log.get("timestamp")
            }
        })

    except Exception as e:
        # Audit the error
        audit_logger.log_error(request, "/assess", str(e))
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@api_bp.route('/rules', methods=['GET'])
@require_api_auth
def api_rules():
    """
    Get the current scoring rules configuration
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        audit_logger.log_request_error(request, "/rules", "Authentication required")
        return jsonify({"error": "Authentication required.", "status": "error"}), 401

    # Audit the request
    audit_logger.log_request(request, "/rules", user_id)

    # Data isolation: Ensure that access to rules is appropriately controlled based on user roles or permissions,
    # although for GETting rules, it's usually broad access. If rules were user-specific, this would be critical.
    # For now, assuming rules are global.

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
    # No authentication or specific data isolation needed for a health check, but can log.
    audit_logger.log_request(request, "/health", "unauthenticated")
    return jsonify({
        "status": "healthy",
        "service": "Qarari Risk Assessment API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })