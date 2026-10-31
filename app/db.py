import sqlite3
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS farmers (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    village   TEXT NOT NULL,
    phone     TEXT,
    milk_type TEXT NOT NULL CHECK (milk_type IN ('cow', 'buffalo')),
    joined_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collections (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id      INTEGER NOT NULL REFERENCES farmers(id),
    collected_on   TEXT NOT NULL,
    shift          TEXT NOT NULL CHECK (shift IN ('morning', 'evening')),
    quantity_litres REAL NOT NULL,
    fat            REAL NOT NULL,
    snf            REAL NOT NULL,
    rate_per_litre REAL NOT NULL,
    amount         REAL NOT NULL,
    UNIQUE (farmer_id, collected_on, shift)
);

CREATE TABLE IF NOT EXISTS payments (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id),
    paid_on   TEXT NOT NULL,
    amount    REAL NOT NULL,
    note      TEXT
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
