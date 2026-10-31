"""All SQL lives here, one repository class per table."""
from .models import Farmer, MilkCollection, Payment


class FarmerRepository:
    def __init__(self, db):
        self.db = db

    def add(self, name, village, phone, milk_type, joined_on):
        cur = self.db.execute(
            "INSERT INTO farmers (name, village, phone, milk_type, joined_on) VALUES (?, ?, ?, ?, ?)",
            (name, village, phone, milk_type, joined_on),
        )
        self.db.commit()
        return self.get(cur.lastrowid)

    def get(self, farmer_id):
        row = self.db.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
        return Farmer.from_row(row) if row else None

    def list(self, village=None):
        if village:
            rows = self.db.execute(
                "SELECT * FROM farmers WHERE village = ? ORDER BY name", (village,)
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM farmers ORDER BY name").fetchall()
        return [Farmer.from_row(r) for r in rows]


class CollectionRepository:
    def __init__(self, db):
        self.db = db

    def add(self, farmer_id, collected_on, shift, quantity, fat, snf, rate, amount):
        cur = self.db.execute(
            """INSERT INTO collections
               (farmer_id, collected_on, shift, quantity_litres, fat, snf, rate_per_litre, amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (farmer_id, collected_on, shift, quantity, fat, snf, rate, amount),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM collections WHERE id = ?", (cur.lastrowid,)).fetchone()
        return MilkCollection.from_row(row)

    def list(self, collected_on=None, farmer_id=None):
        sql, params = "SELECT * FROM collections WHERE 1=1", []
        if collected_on:
            sql += " AND collected_on = ?"
            params.append(collected_on)
        if farmer_id:
            sql += " AND farmer_id = ?"
            params.append(farmer_id)
        sql += " ORDER BY collected_on, shift, id"
        return [MilkCollection.from_row(r) for r in self.db.execute(sql, params).fetchall()]

    def summary(self, farmer_id, start, end):
        row = self.db.execute(
            """SELECT COALESCE(SUM(quantity_litres), 0) AS litres,
                      COALESCE(SUM(amount), 0)          AS amount
               FROM collections
               WHERE farmer_id = ? AND collected_on BETWEEN ? AND ?""",
            (farmer_id, start, end),
        ).fetchone()
        return row["litres"], row["amount"]

    def daily_report(self, day):
        rows = self.db.execute(
            """SELECT shift,
                      COUNT(DISTINCT farmer_id) AS farmers,
                      SUM(quantity_litres)      AS litres,
                      SUM(amount)               AS amount
               FROM collections WHERE collected_on = ? GROUP BY shift""",
            (day,),
        ).fetchall()
        return [dict(r) for r in rows]


class PaymentRepository:
    def __init__(self, db):
        self.db = db

    def add(self, farmer_id, paid_on, amount, note):
        cur = self.db.execute(
            "INSERT INTO payments (farmer_id, paid_on, amount, note) VALUES (?, ?, ?, ?)",
            (farmer_id, paid_on, amount, note),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM payments WHERE id = ?", (cur.lastrowid,)).fetchone()
        return Payment.from_row(row)

    def total(self, farmer_id, start, end):
        row = self.db.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM payments
               WHERE farmer_id = ? AND paid_on BETWEEN ? AND ?""",
            (farmer_id, start, end),
        ).fetchone()
        return row["total"]
