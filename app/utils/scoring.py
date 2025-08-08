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
    try:
        owner1_pct = float(input_data.get("owner1_ownership_pct", 100))
    except (TypeError, ValueError):
        owner1_pct = 100
    owner2_provided = any(
        v is not None and str(v).strip() != ""
        for k, v in input_data.items()
        if k.startswith("owner2_")
    )
    include_owner2 = owner1_pct < 59 and owner2_provided

    for section, fields in rules.items():
        for key, rule in fields.items():
            weight = rule.get("weight", 0)
            value = input_data.get(key)

            if key.startswith("owner2_") and not include_owner2:
                continue

            if key == "years_in_business" and not value:
                if "business_start_date" in input_data:
                    value = calculate_years_in_business(
                        input_data["business_start_date"]
                    )

            if isinstance(value, str):
                val = value.strip().lower()
                if val in ["yes", "true", "good", "passed"]:
                    score += weight
                    value = None  # already handled
                elif val in ["no", "false", "bad", "failed"]:
                    score += 0
                    value = None
                else:
                    # Attempt to treat the string as a numeric value.  If the
                    # conversion fails we simply skip scoring for this field.
                    try:
                        value = float(value)
                    except ValueError:
                        value = None

            if value is not None:
                try:
                    val = float(value)
                    if "utilization" in key:
                        # Lower utilization is better, so award more points for lower values
                        # 0% utilization = full points, 100% utilization = 0 points
                        utilization_score = max(0, weight * (1 - val / 100))
                        score += utilization_score
                    elif "inquiries" in key:
                        # Fewer inquiries is better, award full points for 0-2 inquiries
                        # Gradually reduce points for more inquiries
                        if val <= 2:
                            score += weight
                        elif val <= 5:
                            score += weight * 0.7
                        elif val <= 10:
                            score += weight * 0.3
                        else:
                            score += 0
                    elif "credit_score" in key:
                        # Credit score: 300-850 range, award points proportionally
                        # 720+ = full points, below 600 = minimal points
                        if val >= 720:
                            score += weight
                        elif val >= 680:
                            score += weight * 0.9
                        elif val >= 640:
                            score += weight * 0.7
                        elif val >= 600:
                            score += weight * 0.5
                        elif val >= 500:
                            score += weight * 0.2
                        else:
                            score += 0
                    elif "past_due" in key or "nsf_count" in key:
                        # Lower is better for these fields
                        if val == 0:
                            score += weight
                        elif val <= 1:
                            score += weight * 0.7
                        elif val <= 2:
                            score += weight * 0.4
                        else:
                            score += 0
                    elif "negative_days" in key:
                        # Negative days - fewer is better
                        if val <= 2:
                            score += weight
                        elif val <= 5:
                            score += weight * 0.7
                        elif val <= 10:
                            score += weight * 0.4
                        else:
                            score += 0
                    elif key in ["intelliscore", "stability_score"]:
                        # Business scores: typically 0-100 range
                        if val >= 80:
                            score += weight
                        elif val >= 60:
                            score += weight * 0.8
                        elif val >= 40:
                            score += weight * 0.6
                        else:
                            score += weight * 0.3
                    elif "balance" in key:
                        # Daily average balance scoring - improved ranges
                        if val >= 50000:
                            score += weight
                        elif val >= 25000:
                            score += weight * 0.9
                        elif val >= 10000:
                            score += weight * 0.8
                        elif val >= 5000:
                            score += weight * 0.6
                        elif val >= 1000:
                            score += weight * 0.3
                        else:
                            score += weight * 0.1
                    elif "deposits" in key:
                        # Monthly deposits scoring - improved ranges
                        if val >= 100000:
                            score += weight
                        elif val >= 50000:
                            score += weight * 0.9
                        elif val >= 25000:
                            score += weight * 0.8
                        elif val >= 10000:
                            score += weight * 0.6
                        else:
                            score += weight * 0.3
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
                    elif "value" in key or "amount" in key:
                        # Asset values and amounts
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
                        if val >= 5:
                            score += weight
                        elif val >= 3:
                            score += weight * 0.8
                        elif val >= 2:
                            score += weight * 0.6
                        elif val >= 1:
                            score += weight * 0.4
                        else:
                            score += weight * 0.1
                    else:
                        # Default numeric handling - assume higher is better for remaining fields
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
                except (TypeError, ValueError):
                    pass

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
