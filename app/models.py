"""Plain model classes (OOP). Each wraps one database row."""


class BaseModel:
    fields = ()

    def __init__(self, **kwargs):
        for name in self.fields:
            setattr(self, name, kwargs.get(name))

    @classmethod
    def from_row(cls, row):
        return cls(**{name: row[name] for name in cls.fields})

    def to_dict(self):
        return {name: getattr(self, name) for name in self.fields}


class Farmer(BaseModel):
    fields = ("id", "name", "village", "phone", "milk_type", "joined_on")


class MilkCollection(BaseModel):
    fields = (
        "id", "farmer_id", "collected_on", "shift",
        "quantity_litres", "fat", "snf", "rate_per_litre", "amount",
    )


class Payment(BaseModel):
    fields = ("id", "farmer_id", "paid_on", "amount", "note")
