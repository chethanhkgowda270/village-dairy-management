# Village Dairy Management System

A REST API for a village milk collection centre (dairy cooperative). Farmers bring milk twice a day; the centre records litres, fat % and SNF %, calculates the price, and keeps each farmer's payment balance.

**Tech:** Python, Flask, SQL (SQLite; PostgreSQL-ready), pytest

## Features
- Register farmers (village, cow or buffalo milk)
- Record morning/evening milk collection with automatic price from fat % and SNF %
- Record payments to farmers
- Farmer statement: litres, earnings, payments, balance due
- Daily report for the whole centre

## Concepts used (for interviews)
- **OOP:** `BaseModel` -> `Farmer`, `MilkCollection`, `Payment` (inheritance); `RateStrategy` (abstract class) -> `CowMilkRate`, `BuffaloMilkRate` (polymorphism); repository classes for encapsulating SQL
- **SQL:** 3 tables, foreign keys, CHECK and UNIQUE constraints, `SUM`, `GROUP BY`, `BETWEEN`
- **REST:** proper status codes (201, 400, 404, 409) and JSON validation
- **Testing:** 15 pytest tests, each using a fresh temporary database

## Run
    pip install -r requirements.txt
    python run.py            # then open http://127.0.0.1:5000 in your browser
    python -m pytest         # run tests

The home page is a web interface (Record milk, Farmers, Statement and payments, Daily report). It talks to the REST API below, which you can also call with curl or Postman.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| POST | /farmers | Add farmer |
| GET | /farmers?village=X | List farmers |
| GET | /farmers/<id> | One farmer |
| POST | /collections | Record a milk collection |
| GET | /collections?date=&farmer_id= | List collections |
| POST | /payments | Record a payment |
| GET | /farmers/<id>/statement?from=&to= | Earnings, paid, balance |
| GET | /reports/daily?date= | Centre totals by shift |
| GET | /rate?milk_type=&fat=&snf= | Price per litre (live preview on the web page) |

## Example
    curl -X POST localhost:5000/farmers -H "Content-Type: application/json" \
      -d '{"name":"Ramesh","village":"Hosahalli","phone":"9999999999","milk_type":"cow"}'

    curl -X POST localhost:5000/collections -H "Content-Type: application/json" \
      -d '{"farmer_id":1,"shift":"morning","quantity_litres":10,"fat":4.0,"snf":8.5}'
    # -> rate_per_litre 33.0, amount 330.0

## Pricing
Price per litre = fat % x fat rate + SNF % x SNF rate (see `app/pricing.py`). The rates there are illustrative; use your local dairy's rate chart.

## Ideas to extend
Switch SQLite to PostgreSQL, add login for the centre operator, SMS or PDF payment slips, a simple web dashboard.
