from datetime import datetime

def calculate_years_in_business(start_date):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        today = datetime.today()
        return round((today - start).days / 365.25, 2)
    except Exception:
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

            # Skip owner 2 fields if not relevant
            if key.startswith("owner2_") and not include_owner2:
                continue

            if key == "years_in_business" or key == "business_start_date":
                if not value and "business_start_date" in input_data:
                    value = calculate_years_in_business(input_data["business_start_date"])

            if isinstance(value, str):
                value = value.strip().lower()
                if value in ["yes", "good", "passed", "true"]:
                    score += weight
                elif value in ["no", "bad", "failed", "false"]:
                    score += 0
            elif isinstance(value, (int, float)):
                if "utilization" in key.lower() or "inquiries" in key.lower():
                    score += max(0, weight - (float(value) / 100) * weight)
                else:
                    score += min(float(value), weight)

            max_score += weight

    normalized = round((score / max_score) * 100, 2) if max_score > 0 else 0
    return {
        "total_score": normalized,
        "max_possible": max_score,
        "raw_score": round(score, 2)
    }
