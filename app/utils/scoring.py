
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
                    # Social media fields should have reduced impact
                    if key in ["company_website", "facebook_presence", "linkedin_presence", "review_sites"]:
                        score += weight * 0.7  # Only 70% of weight for social media
                    # Background checks should have full weight
                    elif key in ["criminal_background", "judgment_liens", "contact_verification"]:
                        score += weight
                    else:
                        score += weight * 0.8  # Most yes/no fields get 80% weight
                    max_score += weight
                    continue
                elif val in ["no", "false", "bad", "failed"]:
                    # "No" answers for negative checks (criminal background) should be positive
                    if key in ["criminal_background", "judgment_liens"]:
                        score += weight  # No criminal background is good
                    else:
                        score += 0  # No social media presence is neutral/bad
                    max_score += weight
                    continue
                elif val == "":  # Empty string
                    max_score += weight
                    continue
                elif key == "location_quality":
                    # Location quality scoring
                    max_score += weight
                    if val == "excellent":
                        score += weight
                    elif val == "good":
                        score += weight * 0.8
                    elif val == "fair":
                        score += weight * 0.5
                    elif val == "poor":
                        score += weight * 0.2
                    continue
                elif key == "industry_type":
                    # Industry type scoring - some industries are lower risk
                    max_score += weight
                    if val in ["healthcare", "professional services", "government"]:
                        score += weight  # Low risk industries
                    elif val in ["retail", "manufacturing", "technology", "education"]:
                        score += weight * 0.8  # Moderate risk industries
                    elif val in ["construction", "real estate", "automotive"]:
                        score += weight * 0.6  # Higher risk industries
                    elif val in ["hospitality", "food service", "entertainment"]:
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
                        # More conservative credit score ranges to prevent over-scoring
                        if key.startswith("owner2_"):
                            # Owner 2 gets reduced weight if owner1 is majority owner
                            weight_multiplier = 0.6 if owner1_pct >= 50 else 1.0
                            adjusted_weight = weight * weight_multiplier
                        else:
                            adjusted_weight = weight
                            
                        if val >= 750:
                            score += adjusted_weight
                        elif val >= 700:
                            score += adjusted_weight * 0.9
                        elif val >= 650:
                            score += adjusted_weight * 0.75
                        elif val >= 600:
                            score += adjusted_weight * 0.6
                        elif val >= 550:
                            score += adjusted_weight * 0.4
                        elif val >= 500:
                            score += adjusted_weight * 0.25
                        else:
                            score += adjusted_weight * 0.1
                    elif "past_due" in key or "nsf_count" in key:
                        # Lower is better
                        if val == 0:
                            score += weight
                        elif val <= 1:
                            score += weight * 0.7
                        elif val <= 2:
                            score += weight * 0.4
                        else:
                            score += 0
                    elif "negative_days" in key:
                        # Fewer negative days is better
                        if val <= 2:
                            score += weight
                        elif val <= 5:
                            score += weight * 0.7
                        elif val <= 10:
                            score += weight * 0.4
                        else:
                            score += 0
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
                        # Daily average balance scoring
                        if val >= 25000:
                            score += weight
                        elif val >= 15000:
                            score += weight * 0.9
                        elif val >= 10000:
                            score += weight * 0.8
                        elif val >= 5000:
                            score += weight * 0.6
                        elif val >= 2000:
                            score += weight * 0.4
                        else:
                            score += weight * 0.2
                    elif "deposits" in key or key == "monthly_deposits":
                        # Monthly deposits scoring - more conservative ranges
                        if val >= 100000:
                            score += weight
                        elif val >= 75000:
                            score += weight * 0.95
                        elif val >= 50000:
                            score += weight * 0.85
                        elif val >= 30000:
                            score += weight * 0.75
                        elif val >= 20000:
                            score += weight * 0.6
                        elif val >= 10000:
                            score += weight * 0.45
                        elif val >= 5000:
                            score += weight * 0.3
                        else:
                            score += weight * 0.15
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

    normalized = round((score / max_score) * 100, 2) if max_score else 0
    return {
        "total_score": normalized,
        "raw_score": round(score, 2),
        "max_possible": max_score,
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
