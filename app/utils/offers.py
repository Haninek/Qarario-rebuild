def generate_loan_offers(score: float, input_data: dict = None) -> list[dict]:
    """
    Generate a list of recommended loan offers based on the applicant's
    normalised score and financial capacity (deposits). Higher scores get
    LOWER factor rates. Offers are capped based on monthly deposits.

    Parameters
    ----------
    score: float
        The applicant's total normalised score (0–100).
    input_data: dict
        The input data containing financial information like monthly_deposits

    Returns
    -------
    list[dict]
        A list of loan offer dictionaries with amount, rate, term, and daily payment.
        An empty list indicates the applicant should not receive a loan offer.
    """
    # Applicants scoring below 50 are considered too risky for any offer.
    if score < 50:
        return []

    # Get monthly deposits and frequency for capacity calculation
    monthly_deposits = 0
    deposit_frequency = 0
    if input_data:
        try:
            monthly_deposits = float(input_data.get('monthly_deposits', 0))
        except (TypeError, ValueError):
            monthly_deposits = 0
        try:
            deposit_frequency = float(input_data.get('deposit_frequency', 0))
        except (TypeError, ValueError):
            deposit_frequency = 0

    # AUTOMATIC DECLINE RULES - No offers if these conditions are not met
    if monthly_deposits < 20000:  # Less than $20k monthly deposits = auto decline
        return []
    
    if deposit_frequency < 5:  # Less than 5 deposits per month = auto decline
        return []

    # Calculate max affordable offer based on deposits
    # Ultra conservative: very low limits for small deposit businesses
    if monthly_deposits >= 100000:  # $100k+ deposits
        max_affordable = monthly_deposits * 2.5
    elif monthly_deposits >= 75000:  # $75k+ deposits  
        max_affordable = monthly_deposits * 2
    elif monthly_deposits >= 50000:  # $50k+ deposits
        max_affordable = monthly_deposits * 1.5
    elif monthly_deposits >= 25000:  # $25k+ deposits - MAX 15K OFFERS
        max_affordable = min(15000, monthly_deposits * 0.6)
    elif monthly_deposits >= 15000:  # $15k+ deposits - MAX 10K OFFERS
        max_affordable = min(10000, monthly_deposits * 0.5)
    else:
        max_affordable = min(5000, monthly_deposits * 0.3) if monthly_deposits > 0 else 2500

    # Define tiers with CORRECTED factor rates (higher score = LOWER factor rate)
    tiers = [
        {
            "min": 80,  # Low Risk: 80+ (BEST rates)
            "base_amounts": [150_000, 125_000, 100_000, 75_000, 50_000, 35_000],
            "factor_rate_range": (1.15, 1.35),  # LOW factor rates for high scores
            "term_days": [365, 365, 365, 365, 180, 120]
        },
        {
            "min": 70,  # Moderate Risk: 70-79
            "base_amounts": [100_000, 85_000, 70_000, 50_000, 35_000, 25_000],
            "factor_rate_range": (1.25, 1.45),  # Moderate factor rates
            "term_days": [180, 180, 120, 120, 90, 60]
        },
        {
            "min": 60,  # High Risk: 60-69
            "base_amounts": [75_000, 60_000, 45_000, 35_000, 25_000, 15_000],
            "factor_rate_range": (1.35, 1.55),  # Higher factor rates
            "term_days": [120, 120, 90, 90, 60, 45]
        },
        {
            "min": 50,  # Super High Risk: 50-59 (WORST rates)
            "base_amounts": [35_000, 25_000, 15_000, 10_000, 7_500, 5_000],
            "factor_rate_range": (1.45, 1.70),  # HIGH factor rates for low scores
            "term_days": [90, 60, 60, 45, 30, 30]
        },
    ]

    for tier in tiers:
        if score >= tier["min"]:
            offers = []
            min_factor, max_factor = tier["factor_rate_range"]
            term_days_list = tier["term_days"]

            for i, base_amount in enumerate(tier["base_amounts"]):
                # Cap amount based on monthly deposits capacity
                amount = min(base_amount, max_affordable)

                # Skip offers that are too small to be meaningful
                if amount < 5000:
                    continue

                # Position 1 gets BEST factor rates (lowest), position 6 gets WORST (highest)
                factor_rate_position = i / (len(tier["base_amounts"]) - 1) if len(tier["base_amounts"]) > 1 else 0
                factor_rate = min_factor + (max_factor - min_factor) * factor_rate_position

                # Get term days for this specific offer
                term_days = term_days_list[i] if i < len(term_days_list) else term_days_list[-1]

                # Calculate total repayment amount
                total_repayment = amount * factor_rate

                # Determine payment frequency and calculate payment amount
                # Check if payment amount is reasonable relative to deposits
                if term_days >= 90:  # Longer terms get weekly
                    payment_frequency = "Weekly"
                    weeks = term_days / 7
                    payment_amount = total_repayment / weeks
                    # Weekly payment should not exceed 15% of monthly deposits
                    weekly_deposit_capacity = (monthly_deposits * 0.15) if monthly_deposits > 0 else float('inf')
                    if payment_amount > weekly_deposit_capacity and monthly_deposits > 0:
                        # Reduce amount to fit payment capacity
                        max_weekly_payment = weekly_deposit_capacity
                        max_total_repayment = max_weekly_payment * weeks
                        amount = max_total_repayment / factor_rate
                        total_repayment = amount * factor_rate
                        payment_amount = total_repayment / weeks

                        # Skip if amount becomes too small
                        if amount < 5000:
                            continue
                else:  # Shorter terms get daily
                    payment_frequency = "Daily"
                    payment_amount = total_repayment / term_days
                    # Daily payment should not exceed 5% of monthly deposits / 30 days
                    daily_deposit_capacity = (monthly_deposits * 0.05 / 30) if monthly_deposits > 0 else float('inf')
                    if payment_amount > daily_deposit_capacity and monthly_deposits > 0:
                        # Reduce amount to fit payment capacity
                        max_daily_payment = daily_deposit_capacity
                        max_total_repayment = max_daily_payment * term_days
                        amount = max_total_repayment / factor_rate
                        total_repayment = amount * factor_rate
                        payment_amount = total_repayment / term_days

                        # Skip if amount becomes too small
                        if amount < 5000:
                            continue

                # Calculate buy rate (should be lower than factor rate)
                buy_rate_reduction = 0.05 + (i * 0.01)  # Position 1 gets better buy rate
                buy_rate = max(1.10, factor_rate - buy_rate_reduction)

                offers.append({
                    "amount": round(amount, 0),
                    "factor_rate": round(factor_rate, 2),
                    "term_days": term_days,
                    "payment_amount": round(payment_amount, 2),
                    "payment_frequency": payment_frequency,
                    "total_repayment": round(total_repayment, 2),
                    "buy_rate": round(buy_rate, 2),
                    "commission_percentage": 12,
                    "position": i + 1,
                    "monthly_deposits_used": monthly_deposits,
                    "payment_to_deposit_ratio": round((payment_amount * (4.33 if payment_frequency == "Weekly" else 30)) / monthly_deposits * 100, 1) if monthly_deposits > 0 else 0
                })

            return offers[:6]  # Return max 6 offers

    return []