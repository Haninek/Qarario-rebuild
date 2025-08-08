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
            "min": 80,  # Low Risk: 80+
            "amounts": [150_000, 125_000, 100_000, 75_000, 50_000, 35_000],
            "rate_range": (73.0, 182.5),  # Cash advance rates for low risk
            "term_days": [365, 365, 365, 365, 120, 90]  # First 4 offers get 365 days, last 2 get shorter terms
        },
        {
            "min": 70,  # Moderate Risk: 70-79
            "amounts": [100_000, 85_000, 70_000, 50_000, 35_000, 25_000],
            "rate_range": (146.0, 182.5),  # Cash advance rates for moderate risk
            "term_days": [120, 120, 90, 90, 60, 60]  # Moderate terms 60-120 days
        },
        {
            "min": 60,  # High Risk: 60-69
            "amounts": [75_000, 60_000, 45_000, 35_000, 25_000, 15_000],
            "rate_range": (146.0, 182.5),  # Cash advance rates for high risk
            "term_days": [90, 90, 60, 60, 45, 30]  # Shorter terms 30-90 days
        },
        {
            "min": 50,  # Super High Risk: 50-59
            "amounts": [35_000, 25_000, 15_000, 10_000, 7_500, 5_000],
            "rate_range": (146.0, 182.5),  # Cash advance rates for super high risk
            "term_days": [60, 45, 45, 30, 30, 30]  # Very short terms 30-60 days
        },
    ]

    for tier in tiers:
        if score >= tier["min"]:
            offers = []
            min_rate, max_rate = tier["rate_range"]
            term_days_list = tier["term_days"]

            for i, amount in enumerate(tier["amounts"]):
                # Position 1 gets BEST rates, position 6 gets WORST rates
                # Reverse the rate calculation so early positions get better deals
                rate_factor = (len(tier["amounts"]) - 1 - i) / (len(tier["amounts"]) - 1) if len(tier["amounts"]) > 1 else 0
                annual_rate = min_rate + (max_rate - min_rate) * (1 - rate_factor)  # Reverse the factor

                # Get term days for this specific offer
                term_days = term_days_list[i] if i < len(term_days_list) else term_days_list[-1]

                # Convert annual rate to factor rate for cash advances
                # Factor rate = 1 + (annual_rate / 100) * (term_days / 365)
                factor_rate = 1 + (annual_rate / 100) * (term_days / 365)

                # Calculate total repayment amount
                total_repayment = amount * factor_rate

                # Determine payment frequency and calculate payment amount
                # Mix of daily and weekly payments based on offer position and term
                if i % 2 == 0 and term_days >= 60:  # Even positions with longer terms get weekly
                    payment_frequency = "Weekly"
                    weeks = term_days / 7
                    payment_amount = total_repayment / weeks
                else:  # Odd positions or shorter terms get daily
                    payment_frequency = "Daily"
                    payment_amount = total_repayment / term_days

                # Calculate buy rate (realistic for cash advances)
                # Position 1 gets BEST buy rate (smallest reduction from factor rate)
                buy_rate_reduction = 0.07 + ((len(tier["amounts"]) - 1 - i) * 0.01)  # Reverse: position 1 gets 0.12 reduction, position 6 gets 0.07
                buy_rate = round(factor_rate - buy_rate_reduction, 2)

                offers.append({
                    "amount": amount,
                    "factor_rate": round(factor_rate, 2),
                    "term_days": term_days,
                    "payment_amount": round(payment_amount, 2),
                    "payment_frequency": payment_frequency,
                    "total_repayment": round(total_repayment, 2),
                    "buy_rate": buy_rate,
                    "commission_percentage": 12,
                    "position": i + 1
                })

            return offers

    return []