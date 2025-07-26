
def generate_loan_offers(score):
    if score < 60:
        return []

    tiers = [
        {"min": 90, "offers": [150000, 125000, 100000, 75000, 50000, 35000]},
        {"min": 80, "offers": [100000, 85000, 70000, 50000, 35000, 25000]},
        {"min": 70, "offers": [75000, 60000, 45000, 35000, 25000, 15000]},
        {"min": 60, "offers": [50000, 35000, 25000, 15000, 10000, 5000]}
    ]

    for tier in tiers:
        if score >= tier["min"]:
            return tier["offers"]

    return []
