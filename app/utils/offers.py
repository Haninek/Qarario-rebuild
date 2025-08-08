def generate_loan_offers(score: float) -> list[dict]:
    """
    Generate a list of recommended loan offers based on the applicant's
    normalised score.  Applicants with very low scores are not offered any
    funding.  The threshold has been lowered from 60 to 50 to better
    support moderate‑risk profiles.

    Parameters
    ----------
    score: float
        The applicant's total normalised score (0–100).

    Returns
    -------
    list[dict]
        A list of six loan offer dictionaries with amount, rate, term, and daily payment.
        An empty list indicates the applicant should not receive a loan offer.
    """
    # Applicants scoring below 50 are considered too risky for any offer.
    if score < 50:
        return []

    # Define tiers with amounts and corresponding rates/terms
    tiers = [
        {
            "min": 90,
            "amounts": [150_000, 125_000, 100_000, 75_000, 50_000, 35_000],
            "rate_range": (8.5, 12.5),  # Low risk rates
            "term_days": 365  # 1 year
        },
        {
            "min": 80,
            "amounts": [100_000, 85_000, 70_000, 50_000, 35_000, 25_000],
            "rate_range": (12.0, 16.0),
            "term_days": 365
        },
        {
            "min": 70,
            "amounts": [75_000, 60_000, 45_000, 35_000, 25_000, 15_000],
            "rate_range": (15.5, 20.0),
            "term_days": 365
        },
        {
            "min": 60,
            "amounts": [50_000, 35_000, 25_000, 15_000, 10_000, 5_000],
            "rate_range": (18.0, 24.0),
            "term_days": 365
        },
        {
            "min": 50,
            "amounts": [35_000, 25_000, 15_000, 10_000, 7_500, 5_000],
            "rate_range": (22.0, 30.0),  # High risk rates
            "term_days": 365
        },
    ]

    for tier in tiers:
        if score >= tier["min"]:
            offers = []
            min_rate, max_rate = tier["rate_range"]
            term_days = tier["term_days"]
            
            for i, amount in enumerate(tier["amounts"]):
                # Higher amounts get better rates within the tier
                rate_factor = i / (len(tier["amounts"]) - 1) if len(tier["amounts"]) > 1 else 0
                annual_rate = min_rate + (max_rate - min_rate) * rate_factor
                
                # Calculate daily payment: Principal + Interest / Term
                total_interest = amount * (annual_rate / 100)
                total_amount = amount + total_interest
                daily_payment = total_amount / term_days
                
                offers.append({
                    "amount": amount,
                    "annual_rate": round(annual_rate, 2),
                    "term_days": term_days,
                    "daily_payment": round(daily_payment, 2)
                })
            
            return offers

    return []
