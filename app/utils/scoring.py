
from datetime import datetime
import logging


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
                    # Generic positive responses (for any remaining simple yes/no fields)
                    score += weight * 0.8
                    max_score += weight
                    continue
                elif val in ["no", "false", "bad", "failed"]:
                    # Generic negative responses
                    score += 0
                    max_score += weight
                    continue
                elif val == "":  # Empty string
                    max_score += weight
                    continue
                # Use lookup tables for categorical scoring to reduce branching
                categorical_scoring = {
                    "location_quality": {
                        "excellent": 1.0, "good": 0.8, "fair": 0.5, "poor": 0.2
                    },
                    "review_sites": {
                        "mostly positive": 1.0, "mixed": 0.6, "mostly negative": 0.2, "no reviews": 0.4
                    },
                    "google_business_profile": {
                        "verified/complete": 1.0, "basic": 0.7, "unverified": 0.3, "none": 0.0
                    },
                    "bbb_rating": {
                        "a+/a": 1.0, "a+": 1.0, "a": 1.0,
                        "a-/b+": 0.9, "a-": 0.9, "b+": 0.9,
                        "b/b-": 0.7, "b": 0.7, "b-": 0.7,
                        "c+/c": 0.5, "c+": 0.5, "c": 0.5,
                        "d/f": 0.2, "d": 0.2, "f": 0.2,
                        "not rated": 0.6
                    }
                }
                
                digital_presence_scoring = {
                    "professional": 1.0, "active/professional": 1.0, "complete/active": 1.0,
                    "basic": 0.6, "poor": 0.3, "inactive/poor": 0.3, "incomplete": 0.3, "none": 0.0
                }
                
                if key in categorical_scoring:
                    max_score += weight
                    multiplier = categorical_scoring[key].get(val, 0)
                    score += weight * multiplier
                    continue
                elif key in ["company_website", "facebook_presence", "linkedin_presence"]:
                    max_score += weight
                    multiplier = digital_presence_scoring.get(val, 0)
                    score += weight * multiplier
                    continue
                elif key in ["criminal_background", "judgment_liens", "ucc_filings"]:
                    # Enhanced background check scoring
                    max_score += weight
                    if key == "criminal_background":
                        if val == "clean":
                            score += weight
                        elif val == "minor issues":
                            score += weight * 0.6
                        elif val == "major issues":
                            score += weight * 0.1
                    elif key == "judgment_liens":
                        if val == "none":
                            score += weight
                        elif val == "satisfied/old":
                            score += weight * 0.7
                        elif val == "active/recent":
                            score += weight * 0.2
                    elif key == "ucc_filings":
                        if val == "none":
                            score += weight
                        elif val == "satisfied":
                            score += weight * 0.8
                        elif val == "active":
                            score += weight * 0.5
                    continue
                elif key in ["contact_verification", "business_license_status", "tax_compliance", "professional_liability_insurance"]:
                    # Business verification scoring
                    max_score += weight
                    if val in ["verified", "current/valid", "current", "adequate coverage"]:
                        score += weight
                    elif val in ["partial", "expired/renewing", "minor issues", "basic coverage"]:
                        score += weight * 0.6
                    elif val in ["failed", "issues/invalid", "major issues", "minimal/none"]:
                        score += weight * 0.2
                    continue
                elif key == "industry_type":
                    # Industry type scoring - prioritize receivable-heavy industries
                    max_score += weight
                    # HIGHEST PRIORITY: Receivable-heavy industries with frequent deposits
                    if val in ["restaurants", "restaurant", "food service", "grocery", "retail", "ecommerce", "e-commerce"]:
                        score += weight * 1.2  # BONUS points for receivable-heavy industries
                    elif val in ["healthcare", "professional services", "government"]:
                        score += weight  # Standard low risk industries
                    elif val in ["manufacturing", "technology", "education"]:
                        score += weight * 0.8  # Moderate risk industries
                    elif val in ["construction", "real estate", "automotive"]:
                        score += weight * 0.6  # Higher risk industries
                    elif val in ["hospitality", "entertainment"]:
                        score += weight * 0.4  # High risk industries
                    elif val in ["transportation", "logistics", "agriculture"]:
                        score += weight * 0.5  # Moderate-high risk
                    else:
                        score += weight * 0.3  # Unknown/other industries
                    continue
                else:
                    # Try to convert string to number
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        max_score += weight
                        continue

            # Process numeric values
            if value is not None and value != "":
                try:
                    val = float(value)
                    max_score += weight
                    
                    if "utilization" in key:
                        # Lower utilization is better (0% = full points, 100% = 0 points)
                        utilization_score = max(0, weight * (1 - min(val, 100) / 100))
                        score += utilization_score
                    elif "inquiries" in key:
                        # Fewer inquiries is better
                        if val <= 2:
                            score += weight
                        elif val <= 5:
                            score += weight * 0.7
                        elif val <= 10:
                            score += weight * 0.3
                        else:
                            score += 0
                    elif "credit_score" in key:
                        # Credit score scoring using threshold lookup
                        credit_thresholds = [(750, 1.0), (700, 0.9), (650, 0.75), (600, 0.6), (550, 0.4), (500, 0.25)]
                        multiplier = 0.1  # Default for scores below 500
                        for threshold, mult in credit_thresholds:
                            if val >= threshold:
                                multiplier = mult
                                break
                        score += weight * multiplier
                    elif "past_due" in key or "nsf_count" in key:
                        # NSF count is a critical risk indicator - zero tolerance approach
                        if val == 0:
                            score += weight
                        elif val == 1:
                            score += weight * 0.5  # Reduced from 0.7
                        elif val == 2:
                            score += weight * 0.2  # Reduced from 0.4
                        else:
                            score += 0  # 3+ NSFs is a major red flag
                    elif "negative_days" in key:
                        # Negative days are critical - any negative days indicate cash flow problems
                        if val == 0:
                            score += weight
                        elif val <= 2:
                            score += weight * 0.4  # Reduced from full weight
                        elif val <= 5:
                            score += weight * 0.2  # Reduced from 0.7
                        elif val <= 10:
                            score += weight * 0.1  # Reduced from 0.4
                        else:
                            score += 0  # 10+ negative days is unacceptable
                    elif key in ["intelliscore", "stability_score"]:
                        # Business scores: 0-100 range
                        if val >= 75:
                            score += weight
                        elif val >= 60:
                            score += weight * 0.8
                        elif val >= 45:
                            score += weight * 0.6
                        elif val >= 30:
                            score += weight * 0.4
                        else:
                            score += weight * 0.2
                    elif "balance" in key or key == "daily_average_balance":
                        # Daily average balance scoring using threshold lookup
                        balance_thresholds = [
                            (50000, 1.0), (35000, 0.95), (25000, 0.9), (15000, 0.8),
                            (10000, 0.65), (5000, 0.45), (2000, 0.25)
                        ]
                        multiplier = 0.1  # Default for low balances
                        for threshold, mult in balance_thresholds:
                            if val >= threshold:
                                multiplier = mult
                                break
                        score += weight * multiplier
                    elif "deposits" in key or key == "monthly_deposits":
                        # Monthly deposits scoring using threshold lookup
                        deposit_thresholds = [
                            (150000, 1.0), (100000, 0.95), (75000, 0.9), (50000, 0.85), (40000, 0.75),
                            (30000, 0.6), (25000, 0.4), (20000, 0.25), (15000, 0.2), (10000, 0.15), (5000, 0.1)
                        ]
                        multiplier = 0.05  # Default for very low deposits
                        for threshold, mult in deposit_thresholds:
                            if val >= threshold:
                                multiplier = mult
                                break
                        score += weight * multiplier
                    elif "frequency" in key:
                        # Deposit frequency - higher frequency is better
                        if val >= 15:
                            score += weight
                        elif val >= 10:
                            score += weight * 0.8
                        elif val >= 5:
                            score += weight * 0.6
                        else:
                            score += weight * 0.3
                    elif "distance" in key:
                        # Distance from residence - closer is better
                        if val <= 5:
                            score += weight
                        elif val <= 15:
                            score += weight * 0.8
                        elif val <= 30:
                            score += weight * 0.5
                        else:
                            score += weight * 0.2
                    elif "value" in key or "amount" in key or "capital" in key or "collateral" in key or key in ["real_estate_value", "equipment_value", "inventory_value", "liquid_assets", "asset_value", "business_assets"]:
                        # Asset values including capital & collateral
                        if val >= 100000:
                            score += weight
                        elif val >= 50000:
                            score += weight * 0.8
                        elif val >= 25000:
                            score += weight * 0.6
                        elif val >= 10000:
                            score += weight * 0.4
                        else:
                            score += weight * 0.2
                    elif "years" in key:
                        # Years in business
                        if val >= 3:
                            score += weight
                        elif val >= 2:
                            score += weight * 0.8
                        elif val >= 1:
                            score += weight * 0.6
                        elif val >= 0.5:
                            score += weight * 0.4
                        else:
                            score += weight * 0.2
                    else:
                        # Default numeric handling
                        if "percentage" in key or "pct" in key:
                            # Percentage fields (0-100 range)
                            if val >= 80:
                                score += weight
                            elif val >= 60:
                                score += weight * 0.8
                            elif val >= 40:
                                score += weight * 0.6
                            elif val >= 20:
                                score += weight * 0.4
                            else:
                                score += weight * 0.2
                        else:
                            # Generic numeric fields - assume higher is better
                            if val >= 80:
                                score += weight
                            elif val >= 60:
                                score += weight * 0.8
                            elif val >= 40:
                                score += weight * 0.6
                            elif val >= 20:
                                score += weight * 0.4
                            else:
                                score += weight * 0.2
                except (TypeError, ValueError, AttributeError):
                    # If we can't convert to float, still count max_score for non-underwriter fields
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
