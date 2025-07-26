
from datetime import datetime

def calculate_years_in_business(start_date):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        today = datetime.today()
        return round((today - start).days / 365.25, 2)
    except:
        return 0

def calculate_score(input_data, rules):
    score = 0
    max_score = 0
    owner1_pct = float(input_data.get("owner1_ownership_pct", 100))
    include_owner2 = owner1_pct < 59

    for section, fields in rules.items():
        for key, rule in fields.items():
            weight = rule.get("weight", 0)
            value = input_data.get(key)

            # Skip Owner 2 fields if not needed
            if key.startswith("owner2_") and not include_owner2:
                continue

            # Auto-fill years in business
            if key == "years_in_business" and not value:
                if "business_start_date" in input_data:
                    value = calculate_years_in_business(input_data["business_start_date"])

            if isinstance(value, str):
                val = value.strip().lower()
                if val in ["yes", "true", "good", "passed"]:
                    score += weight
                elif val in ["no", "false", "bad", "failed"]:
                    score += 0
            elif isinstance(value, (int, float, str)):
                try:
                    val = float(value)
                    if "utilization" in key or "inquiries" in key:
                        score += max(0, weight - (val / 100) * weight)
                    else:
                        score += min(val, weight)
                except:
                    pass

            max_score += weight

    normalized = round((score / max_score) * 100, 2) if max_score else 0
    return {
        "total_score": normalized,
        "raw_score": round(score, 2),
        "max_possible": max_score
    }
