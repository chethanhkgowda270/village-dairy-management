import pytest

from app.pricing import BuffaloMilkRate, CowMilkRate, RateStrategy, get_strategy


def test_cow_rate():
    assert CowMilkRate().rate_per_litre(4.0, 8.5) == 33.0


def test_buffalo_rate_is_higher_for_richer_milk():
    assert BuffaloMilkRate().rate_per_litre(6.5, 9.0) == 45.3


def test_get_strategy_is_polymorphic():
    assert isinstance(get_strategy("cow"), RateStrategy)
    assert isinstance(get_strategy("buffalo"), RateStrategy)


def test_unknown_milk_type():
    with pytest.raises(ValueError):
        get_strategy("goat")
