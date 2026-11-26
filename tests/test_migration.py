"""Upgrading a database created by an earlier release must keep every record.

Runs in a subprocess because importing app.py opens the database at import time.
Requires the full requirements.txt.
"""
import os
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LEGACY_SCHEMA = """
CREATE TABLE user (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE, phone VARCHAR(30), password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, created_at DATETIME);
CREATE TABLE shop (id INTEGER PRIMARY KEY, name VARCHAR(140) NOT NULL, owner_name VARCHAR(100) NOT NULL,
    category VARCHAR(60) NOT NULL, description TEXT, city VARCHAR(80) NOT NULL, area VARCHAR(100),
    address VARCHAR(255), phone VARCHAR(30), approved BOOLEAN, created_at DATETIME);
CREATE TABLE "order" (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, shop_id INTEGER NOT NULL,
    delivery_partner_id INTEGER, customer_name VARCHAR(100) NOT NULL, phone VARCHAR(30),
    delivery_address VARCHAR(255) NOT NULL, city VARCHAR(80) NOT NULL, total NUMERIC(10, 2) NOT NULL,
    status VARCHAR(30), payment_method VARCHAR(30), created_at DATETIME);
INSERT INTO user (id, name, email, password_hash, role) VALUES (1, 'Old Owner', 'old@example.com', 'x', 'admin');
INSERT INTO shop (id, name, owner_name, category, city, approved) VALUES (1, 'Old Shop', 'Old Owner', 'Groceries', 'Madurai', 1);
INSERT INTO "order" (id, customer_id, shop_id, customer_name, delivery_address, city, total, status)
    VALUES (1, 1, 1, 'Old Owner', 'Old Street', 'Madurai', 115.00, 'Delivered');
"""

CHECK = textwrap.dedent("""
    import sys
    sys.path.insert(0, {root!r})
    import app as application
    from models import db, Shop, Order
    with application.app.app_context():
        shop = db.session.get(Shop, 1)
        order = db.session.get(Order, 1)
        print(shop.country, shop.currency, shop.timezone, order.currency, order.timezone, order.status)
""")


def test_legacy_database_is_upgraded_without_losing_records(tmp_path):
    db_file = tmp_path / "legacy.db"
    connection = sqlite3.connect(db_file)
    connection.executescript(LEGACY_SCHEMA)
    connection.commit()
    connection.close()

    env = dict(os.environ,
               DATABASE_URL=f"sqlite:///{db_file.as_posix()}",
               NEARBUY_DATA_DIR=str(tmp_path / "data"),
               NEARBUY_OPEN_BROWSER="0")
    result = subprocess.run([sys.executable, "-c", CHECK.format(root=str(ROOT))],
                            env=env, capture_output=True, text=True, cwd=str(ROOT))
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["IN", "INR", "Asia/Kolkata", "INR", "Asia/Kolkata", "Delivered"]

    connection = sqlite3.connect(db_file)
    shop_columns = {row[1] for row in connection.execute("PRAGMA table_info(shop)")}
    assert {"country", "currency", "timezone"} <= shop_columns
    total = connection.execute('SELECT total FROM "order" WHERE id = 1').fetchone()[0]
    assert float(total) == 115.0
    connection.close()
