import sqlite3
from datetime import date

from flask import Blueprint, jsonify, request

from .db import get_db
from .pricing import get_strategy
from .repository import CollectionRepository, FarmerRepository, PaymentRepository

bp = Blueprint("api", __name__)

SHIFTS = ("morning", "evening")
MILK_TYPES = ("cow", "buffalo")


class ValidationError(Exception):
    pass


@bp.errorhandler(ValidationError)
def handle_validation(err):
    return jsonify(error=str(err)), 400


@bp.errorhandler(sqlite3.IntegrityError)
def handle_integrity(_err):
    return jsonify(error="Entry already exists for this farmer, date and shift"), 409


# ---------- helpers ----------
def _body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def _text(data, key, required=True):
    value = data.get(key)
    if value is None or str(value).strip() == "":
        if required:
            raise ValidationError(f"'{key}' is required")
        return None
    return str(value).strip()


def _number(data, key, low, high):
    try:
        value = float(data[key])
    except (KeyError, TypeError, ValueError):
        raise ValidationError(f"'{key}' must be a number")
    if not (low < value <= high):
        raise ValidationError(f"'{key}' must be greater than {low} and at most {high}")
    return value


def _iso_date(value, key="date"):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValidationError(f"'{key}' must be a date in YYYY-MM-DD format")


def _repos():
    db = get_db()
    return FarmerRepository(db), CollectionRepository(db), PaymentRepository(db)


def _farmer_or_404(farmers, farmer_id):
    farmer = farmers.get(farmer_id)
    if farmer is None:
        return None, (jsonify(error="Farmer not found"), 404)
    return farmer, None


# ---------- farmers ----------
@bp.post("/farmers")
def add_farmer():
    data = _body()
    milk_type = _text(data, "milk_type").lower()
    if milk_type not in MILK_TYPES:
        raise ValidationError(f"'milk_type' must be one of {MILK_TYPES}")
    farmers, _, _ = _repos()
    farmer = farmers.add(
        _text(data, "name"),
        _text(data, "village"),
        _text(data, "phone", required=False),
        milk_type,
        date.today().isoformat(),
    )
    return jsonify(farmer.to_dict()), 201


@bp.get("/farmers")
def list_farmers():
    farmers, _, _ = _repos()
    return jsonify([f.to_dict() for f in farmers.list(request.args.get("village"))])


@bp.get("/farmers/<int:farmer_id>")
def get_farmer(farmer_id):
    farmers, _, _ = _repos()
    farmer, err = _farmer_or_404(farmers, farmer_id)
    return err if err else jsonify(farmer.to_dict())


# ---------- milk collection ----------
@bp.post("/collections")
def add_collection():
    data = _body()
    farmers, collections, _ = _repos()
    try:
        farmer_id = int(data.get("farmer_id"))
    except (TypeError, ValueError):
        raise ValidationError("'farmer_id' must be an integer")
    farmer, err = _farmer_or_404(farmers, farmer_id)
    if err:
        return err

    shift = _text(data, "shift").lower()
    if shift not in SHIFTS:
        raise ValidationError(f"'shift' must be one of {SHIFTS}")
    day = _iso_date(data.get("date", date.today().isoformat()))
    quantity = _number(data, "quantity_litres", 0, 500)
    fat = _number(data, "fat", 0, 12)
    snf = _number(data, "snf", 0, 12)

    rate = get_strategy(farmer.milk_type).rate_per_litre(fat, snf)
    amount = round(quantity * rate, 2)
    record = collections.add(farmer.id, day, shift, quantity, fat, snf, rate, amount)
    return jsonify(record.to_dict()), 201


@bp.get("/collections")
def list_collections():
    _, collections, _ = _repos()
    day = request.args.get("date")
    if day:
        day = _iso_date(day)
    farmer_id = request.args.get("farmer_id", type=int)
    return jsonify([c.to_dict() for c in collections.list(day, farmer_id)])


# ---------- payments ----------
@bp.post("/payments")
def add_payment():
    data = _body()
    farmers, _, payments = _repos()
    try:
        farmer_id = int(data.get("farmer_id"))
    except (TypeError, ValueError):
        raise ValidationError("'farmer_id' must be an integer")
    farmer, err = _farmer_or_404(farmers, farmer_id)
    if err:
        return err
    amount = _number(data, "amount", 0, 10_000_000)
    day = _iso_date(data.get("date", date.today().isoformat()))
    payment = payments.add(farmer.id, day, amount, _text(data, "note", required=False))
    return jsonify(payment.to_dict()), 201


# ---------- price preview ----------
@bp.get("/rate")
def rate_preview():
    """Price per litre for a milk type, fat % and SNF % (used by the web page's live preview)."""
    milk_type = (request.args.get("milk_type") or "").lower()
    if milk_type not in MILK_TYPES:
        raise ValidationError(f"'milk_type' must be one of {MILK_TYPES}")
    try:
        fat, snf = float(request.args["fat"]), float(request.args["snf"])
    except (KeyError, ValueError):
        raise ValidationError("'fat' and 'snf' must be numbers")
    if not (0 < fat <= 12 and 0 < snf <= 12):
        raise ValidationError("'fat' and 'snf' must be greater than 0 and at most 12")
    return jsonify(rate_per_litre=get_strategy(milk_type).rate_per_litre(fat, snf))


# ---------- reports ----------
@bp.get("/farmers/<int:farmer_id>/statement")
def statement(farmer_id):
    """Earnings, payments and balance for a period (default: the current month)."""
    farmers, collections, payments = _repos()
    farmer, err = _farmer_or_404(farmers, farmer_id)
    if err:
        return err
    today = date.today()
    start = _iso_date(request.args.get("from", today.replace(day=1).isoformat()), "from")
    end = _iso_date(request.args.get("to", today.isoformat()), "to")

    litres, earned = collections.summary(farmer_id, start, end)
    paid = payments.total(farmer_id, start, end)
    return jsonify(
        farmer=farmer.to_dict(),
        period={"from": start, "to": end},
        total_litres=round(litres, 2),
        total_earned=round(earned, 2),
        total_paid=round(paid, 2),
        balance_due=round(earned - paid, 2),
    )


@bp.get("/reports/daily")
def daily_report():
    _, collections, _ = _repos()
    day = _iso_date(request.args.get("date", date.today().isoformat()))
    shifts = collections.daily_report(day)
    return jsonify(
        date=day,
        shifts=shifts,
        total_litres=round(sum(s["litres"] for s in shifts), 2),
        total_amount=round(sum(s["amount"] for s in shifts), 2),
    )
