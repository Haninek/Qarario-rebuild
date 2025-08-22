
from datetime import datetime
import logging

# Optimized scoring lookup tables
CREDIT_SCORE_THRESHOLDS = [(750, 1.0), (700, 0.9), (650, 0.75), (600, 0.6), (550, 0.4), (500, 0.25)]
BALANCE_THRESHOLDS = [(50000, 1.0), (35000, 0.95), (25000, 0.9), (15000, 0.8), (10000, 0.65), (5000, 0.45), (2000, 0.25)]
DEPOSIT_THRESHOLDS = [(150000, 1.0), (100000, 0.95), (75000, 0.9), (50000, 0.85), (40000, 0.75), (30000, 0.6), (25000, 0.4), (20000, 0.25), (15000, 0.2), (10000, 0.15), (5000, 0.1)]

CATEGORICAL_SCORING = {
    "location_quality": {"excellent": 1.0, "good": 0.8, "fair": 0.5, "poor": 0.2},
    "review_sites": {"mostly positive": 1.0, "mixed": 0.6, "mostly negative": 0.2, "no reviews": 0.4},
    "google_business_profile": {"verified/complete": 1.0, "basic": 0.7, "unverified": 0.3, "none": 0.0},
    "bbb_rating": {"a+/a": 1.0, "a+": 1.0, "a": 1.0, "a-/b+": 0.9, "a-": 0.9, "b+": 0.9, "b/b-": 0.7, "b": 0.7, "b-": 0.7, "c+/c": 0.5, "c+": 0.5, "c": 0.5, "d/f": 0.2, "d": 0.2, "f": 0.2, "not rated": 0.6}
}

DIGITAL_PRESENCE_SCORING = {
    "professional": 1.0, "active/professional": 1.0, "complete/active": 1.0,
    "basic": 0.6, "poor": 0.3, "inactive/poor": 0.3, "incomplete": 0.3, "none": 0.0
}

BACKGROUND_CHECK_SCORING = {
    "criminal_background": {"clean": 1.0, "minor issues": 0.6, "major issues": 0.1},
    "judgment_liens": {"none": 1.0, "satisfied/old": 0.7, "active/recent": 0.2},
    "ucc_filings": {"none": 1.0, "satisfied": 0.8, "active": 0.5}
}

VERIFICATION_SCORING = {
    "verified": 1.0, "current/valid": 1.0, "current": 1.0, "adequate coverage": 1.0,
    "partial": 0.6, "expired/renewing": 0.6, "minor issues": 0.6, "basic coverage": 0.6,
    "failed": 0.2, "issues/invalid": 0.2, "major issues": 0.2, "minimal/none": 0.2
}

INDUSTRY_SCORING = {
    # HIGHEST PRIORITY: Receivable-heavy industries with frequent deposits  
    "restaurants": 1.2, "restaurant": 1.2, "food service": 1.2, "grocery": 1.2, "retail": 1.2, "ecommerce": 1.2, "e-commerce": 1.2,
    # Standard low risk industries
    "healthcare": 1.0, "professional services": 1.0, "government": 1.0,
    # Moderate risk industries
    "manufacturing": 0.8, "technology": 0.8, "education": 0.8,
    # Higher risk industries
    "construction": 0.6, "real estate": 0.6, "automotive": 0.6,
    # High risk industries
    "hospitality": 0.4, "entertainment": 0.4,
    # Moderate-high risk
    "transportation": 0.5, "logistics": 0.5, "agriculture": 0.5
}

def score_threshold_lookup(value, thresholds, default=0.1):
    """Generic threshold-based scoring lookup"""
    for threshold, multiplier in thresholds:
        if value >= threshold:
            return multiplier
    return default

def score_categorical_lookup(key, value, scoring_dict, default=0):
    """Generic categorical scoring lookup"""
    return scoring_dict.get(key, {}).get(value.lower(), default)

def score_credit_field(key, value, weight):
    """Optimized credit field scoring"""
    if "credit_score" in key:
        return weight * score_threshold_lookup(value, CREDIT_SCORE_THRESHOLDS)
    elif "utilization" in key:
        return max(0, weight * (1 - min(value, 100) / 100))
    elif "inquiries" in key:
        if value <= 2: return weight
        elif value <= 5: return weight * 0.7
        elif value <= 10: return weight * 0.3
        else: return 0
    elif "past_due" in key:
        if value == 0: return weight
        elif value == 1: return weight * 0.5
        elif value == 2: return weight * 0.2
        else: return 0
    return 0

def score_bank_field(key, value, weight):
    """Optimized bank analysis scoring"""
    if "balance" in key or key == "daily_average_balance":
        return weight * score_threshold_lookup(value, BALANCE_THRESHOLDS)
    elif "deposits" in key or key == "monthly_deposits":
        return weight * score_threshold_lookup(value, DEPOSIT_THRESHOLDS, 0.05)
    elif "nsf_count" in key:
        if value == 0: return weight
        elif value == 1: return weight * 0.5
        elif value == 2: return weight * 0.2
        else: return 0
    elif "negative_days" in key:
        if value == 0: return weight
        elif value <= 2: return weight * 0.4
        elif value <= 5: return weight * 0.2
        elif value <= 10: return weight * 0.1
        else: return 0
    elif "frequency" in key:
        if value >= 15: return weight
        elif value >= 10: return weight * 0.8
        elif value >= 5: return weight * 0.6
        else: return weight * 0.3
    return 0

def score_business_field(key, value, weight):
    """Optimized business information scoring"""
    if key in ["intelliscore", "stability_score"]:
        if value >= 75: return weight
        elif value >= 60: return weight * 0.8
        elif value >= 45: return weight * 0.6
        elif value >= 30: return weight * 0.4
        else: return weight * 0.2
    elif "years" in key:
        if value >= 3: return weight
        elif value >= 2: return weight * 0.8
        elif value >= 1: return weight * 0.6
        elif value >= 0.5: return weight * 0.4
        else: return weight * 0.2
    return 0


def calculate_years_in_business(start_date):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        today = datetime.today()
        return round((today - start).days / 365.25, 2)
    except ValueError:
        return 0
    except Exception:
        logging.exception("Unexpected error calculating years in business")
        raise


def calculate_score(input_data, rules):
    score = 0
    max_score = 0
    
    # Parse owner1 ownership percentage
    try:
        owner1_pct = float(input_data.get("owner1_ownership_pct", 100))
    except (TypeError, ValueError):
        owner1_pct = 100
    
    # Check if owner2 data is provided AND owner1 owns less than 50%
    owner2_provided = any(
        v is not None and str(v).strip() != ""
        for k, v in input_data.items()
        if k.startswith("owner2_") and k != "owner2_ownership_pct"  # Don't count just ownership pct
    )
    include_owner2 = owner1_pct < 50 and owner2_provided

    for section, fields in rules.items():
        for key, rule in fields.items():
            weight = rule.get("weight", 0)
            value = input_data.get(key)

            # Skip owner2 fields unless conditions are met
            if key.startswith("owner2_") and not include_owner2:
                continue

            # Handle years in business calculation
            if key == "years_in_business" and not value:
                if "business_start_date" in input_data:
                    value = calculate_years_in_business(input_data["business_start_date"])

            # Convert string values to appropriate types
            if isinstance(value, str):
                val = value.strip().lower()
                if val in ["yes", "true", "good", "passed"]:
                    score += weight * 0.8
                    max_score += weight
                    continue
                elif val in ["no", "false", "bad", "failed"]:
                    score += 0
                    max_score += weight
                    continue
                elif val == "":
                    max_score += weight
                    continue
                
                # Use optimized lookup tables
                max_score += weight
                
                # Check categorical scoring
                if key in CATEGORICAL_SCORING:
                    multiplier = CATEGORICAL_SCORING[key].get(val, 0)
                    score += weight * multiplier
                    continue
                elif key in ["company_website", "facebook_presence", "linkedin_presence"]:
                    multiplier = DIGITAL_PRESENCE_SCORING.get(val, 0)
                    score += weight * multiplier
                    continue
                elif key in BACKGROUND_CHECK_SCORING:
                    multiplier = BACKGROUND_CHECK_SCORING[key].get(val, 0)
                    score += weight * multiplier
                    continue
                elif key in ["contact_verification", "business_license_status", "tax_compliance", "professional_liability_insurance"]:
                    multiplier = VERIFICATION_SCORING.get(val, 0)
                    score += weight * multiplier
                    continue
                elif key == "industry_type":
                    multiplier = INDUSTRY_SCORING.get(val, 0.3)  # Default for unknown industries
                    score += weight * multiplier
                    continue
                else:
                    # Try to convert string to number
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        continue

            # Process numeric values
            if value is not None and value != "":
                try:
                    val = float(value)
                    max_score += weight
                    
                    # Use optimized helper functions based on field type
                    if any(credit_key in key for credit_key in ["credit_score", "utilization", "inquiries", "past_due"]):
                        score += score_credit_field(key, val, weight)
                    elif any(bank_key in key for bank_key in ["balance", "deposits", "nsf_count", "negative_days", "frequency"]):
                        score += score_bank_field(key, val, weight)
                    elif key in ["intelliscore", "stability_score"] or "years" in key:
                        score += score_business_field(key, val, weight)
                    elif "distance" in key:
                        # Distance scoring
                        if val <= 5: score += weight
                        elif val <= 15: score += weight * 0.8
                        elif val <= 30: score += weight * 0.5
                        else: score += weight * 0.2
                    elif any(asset_key in key for asset_key in ["value", "amount", "capital", "collateral"]) or key in ["real_estate_value", "equipment_value", "inventory_value", "liquid_assets", "asset_value", "business_assets"]:
                        # Asset values
                        if val >= 100000: score += weight
                        elif val >= 50000: score += weight * 0.8
                        elif val >= 25000: score += weight * 0.6
                        elif val >= 10000: score += weight * 0.4
                        else: score += weight * 0.2
                    else:
                        # Default numeric handling
                        if "percentage" in key or "pct" in key:
                            if val >= 80: score += weight
                            elif val >= 60: score += weight * 0.8
                            elif val >= 40: score += weight * 0.6
                            elif val >= 20: score += weight * 0.4
                            else: score += weight * 0.2
                        else:
                            if val >= 80: score += weight
                            elif val >= 60: score += weight * 0.8
                            elif val >= 40: score += weight * 0.6
                            elif val >= 20: score += weight * 0.4
                            else: score += weight * 0.2
                except (TypeError, ValueError, AttributeError):
                    if key != "underwriter_adjustment":
                        max_score += weight
                    continue
            else:
                # Field not provided - only count towards max possible if not underwriter_adjustment
                if key != "underwriter_adjustment":
                    max_score += weight

    # Check for automatic decline conditions
    monthly_deposits = 0
    deposit_frequency = 0
    try:
        monthly_deposits = float(input_data.get('monthly_deposits', 0))
    except (TypeError, ValueError):
        monthly_deposits = 0
    try:
        deposit_frequency = float(input_data.get('deposit_frequency', 0))
    except (TypeError, ValueError):
        deposit_frequency = 0

    # Auto-decline flags
    auto_decline_reasons = []
    if monthly_deposits < 20000:
        auto_decline_reasons.append("Monthly deposits below $20,000 minimum")
    if deposit_frequency < 5:
        auto_decline_reasons.append("Deposit frequency below 5 per month minimum")

    normalized = round((score / max_score) * 100, 2) if max_score else 0
    
    # If auto-decline conditions are met, force score to 0
    if auto_decline_reasons:
        normalized = 0

    return {
        "total_score": normalized,
        "raw_score": round(score, 2),
        "max_possible": max_score,
        "auto_decline": len(auto_decline_reasons) > 0,
        "decline_reasons": auto_decline_reasons
    }


def classify_risk(score: float) -> str:
    """Classify a normalised score into a risk tier.

    Parameters
    ----------
    score: float
        The applicant's total normalised score (0–100).

    Returns
    -------
    str
        One of ``"low"``, ``"moderate"``, ``"high"`` or ``"super_high"``
        representing the risk tier.  The tiers align with the loan offer
        thresholds used elsewhere in the application.
    """

    if score >= 80:
        return "low"
    if score >= 60:
        return "moderate"
    if score >= 50:
        return "high"
    return "super_high"
