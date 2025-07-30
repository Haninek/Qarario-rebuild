def generate_loan_offers(score: float) -> list[int]:
    """
    Generate a list of recommended loan amounts based on the applicant's
    normalised score.  Applicants with very low scores are not offered any
    funding.  The threshold has been lowered from 60 to 50 to better
    support moderate‑risk profiles.

    Parameters
    ----------
    score: float
        The applicant's total normalised score (0–100).

    Returns
    -------
    list[int]
        A list of six descending loan amounts in dollars.  An empty list
        indicates the applicant should not receive a loan offer.
    """
    # Applicants scoring below 50 are considered too risky for any offer.
    if score < 50:
        return []

    tiers = [
        {
            "min": 90,
            "offers": [150_000, 125_000, 100_000, 75_000, 50_000, 35_000],
        },
        {
            "min": 80,
            "offers": [100_000, 85_000, 70_000, 50_000, 35_000, 25_000],
        },
        {
            "min": 70,
            "offers": [75_000, 60_000, 45_000, 35_000, 25_000, 15_000],
        },
        {
            "min": 60,
            "offers": [50_000, 35_000, 25_000, 15_000, 10_000, 5_000],
        },
        {
            "min": 50,
            "offers": [35_000, 25_000, 15_000, 10_000, 7_500, 5_000],
        },
    ]

    for tier in tiers:
        if score >= tier["min"]:
            return tier["offers"]

    return []
