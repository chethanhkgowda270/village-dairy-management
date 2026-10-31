"""Milk pricing. Uses inheritance + polymorphism: each milk type has its own rate strategy."""
from abc import ABC, abstractmethod


class RateStrategy(ABC):
    """Base class: every milk type must say how it turns fat% and SNF% into a price per litre."""

    milk_type = ""

    @abstractmethod
    def rate_per_litre(self, fat: float, snf: float) -> float:
        ...


class FatSnfRate(RateStrategy):
    """Price = (fat% x rate per fat point) + (SNF% x rate per SNF point).

    The rates below are illustrative. Real societies set them from the
    dairy federation's rate chart, so change them to match.
    """

    fat_rate = 0.0
    snf_rate = 0.0

    def rate_per_litre(self, fat: float, snf: float) -> float:
        return round(fat * self.fat_rate + snf * self.snf_rate, 2)


class CowMilkRate(FatSnfRate):
    milk_type = "cow"
    fat_rate = 4.0
    snf_rate = 2.0


class BuffaloMilkRate(FatSnfRate):
    milk_type = "buffalo"
    fat_rate = 4.2
    snf_rate = 2.0


_STRATEGIES = {s.milk_type: s() for s in (CowMilkRate, BuffaloMilkRate)}


def get_strategy(milk_type: str) -> RateStrategy:
    try:
        return _STRATEGIES[milk_type]
    except KeyError:
        raise ValueError(f"Unknown milk type: {milk_type}")
