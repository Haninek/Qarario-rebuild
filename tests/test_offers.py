import pytest

from app.utils.offers import generate_loan_offers


def test_no_offers_below_threshold():
    assert generate_loan_offers(49.9) == []


def test_offers_at_exact_threshold():
    expected = [35000, 25000, 15000, 10000, 7500, 5000]
    assert generate_loan_offers(50) == expected


def test_offers_between_50_and_60():
    expected = [35000, 25000, 15000, 10000, 7500, 5000]
    assert generate_loan_offers(55) == expected


def test_next_tier_at_60():
    expected = [50000, 35000, 25000, 15000, 10000, 5000]
    assert generate_loan_offers(60) == expected
