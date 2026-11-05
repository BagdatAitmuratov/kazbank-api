"""KazBank: схеманы жасайды және бастапқы деректерді толтырады.

Іске қосу:
    python init_db.py                  # DATABASE_URL .env файлынан алынады
    python init_db.py "<conninfo>"     # немесе нақты қосылым жолын беруге болады
"""
import os
import sys
from decimal import Decimal

import psycopg
from dotenv import load_dotenv
from psycopg import errors

load_dotenv(override=True)

DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    city        TEXT DEFAULT 'Almaty',
    email       TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id     SERIAL PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    account_number TEXT NOT NULL UNIQUE,
    balance        NUMERIC(15,2) DEFAULT 0 CHECK (balance >= 0)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id     INTEGER NOT NULL REFERENCES accounts(account_id),
    amount         NUMERIC(15,2) NOT NULL,
    tx_type        TEXT NOT NULL CHECK (tx_type IN ('debit', 'credit')),
    created_at     TIMESTAMP DEFAULT now()
);
"""

# (full_name, city, email)
SEED_CUSTOMERS = [
    ("Arman Bekov",     "Almaty",    "arman.bekov@kazbank.kz"),
    ("Zarina Seiit",    "Astana",    "zarina.seiit@kazbank.kz"),
    ("Daniyar Nurlan",  "Shymkent",  "daniyar.nurlan@kazbank.kz"),
    ("Aigerim Sultan",  "Almaty",    "aigerim.sultan@kazbank.kz"),
    ("Nursultan Omar",  "Karaganda", "nursultan.omar@kazbank.kz"),
    ("Madina Kaiyr",    "Almaty",    "madina.kaiyr@kazbank.kz"),
    ("Yerlan Abdi",     "Astana",    "yerlan.abdi@kazbank.kz"),
    ("Aliya Temir",     "Aktobe",    "aliya.temir@kazbank.kz"),
    ("Bauyrzhan Askar", "Shymkent",  "bauyrzhan.askar@kazbank.kz"),
    ("Dana Rakhim",     "Almaty",    "dana.rakhim@kazbank.kz"),
]

# (клиенттің реттік нөмірі 1..10, account_number, balance)
SEED_ACCOUNTS = [
    (1, "KZ0001", "450000.00"), (1, "KZ0002", "120000.00"),
    (2, "KZ0003", "300000.00"), (2, "KZ0004", "75000.00"),
    (3, "KZ0005", "1000000.00"), (3, "KZ0006", "30000.00"),
    (4, "KZ0007", "420000.00"), (4, "KZ0008", "15000.00"),
    (5, "KZ0009", "90000.00"), (5, "KZ0010", "310000.00"),
    (6, "KZ0011", "670000.00"),
    (7, "KZ0012", "45000.00"),
    (8, "KZ0013", "800000.00"),
    (9, "KZ0014", "220000.00"),
    (10, "KZ0015", "150000.00"),
]


def main():
    conninfo = sys.argv[1] if len(sys.argv) > 1 else os.environ["DATABASE_URL"]

    with psycopg.connect(conninfo) as conn:
        # 1) Схема
        conn.execute(DDL)
        print("Схема жасалды (customers, accounts, transactions).")

        # 2) Seed (тек кесте бос болса)
        count = conn.execute("SELECT count(*) FROM customers").fetchone()[0]
        if count == 0:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO customers (full_name, city, email) VALUES (%s, %s, %s)",
                    SEED_CUSTOMERS,
                )
                cur.execute("SELECT customer_id FROM customers ORDER BY customer_id")
                ids = [r[0] for r in cur.fetchall()]
                cur.executemany(
                    "INSERT INTO accounts (customer_id, account_number, balance) VALUES (%s, %s, %s)",
                    [(ids[idx - 1], number, Decimal(bal)) for idx, number, bal in SEED_ACCOUNTS],
                )
            print(f"Толтырылды: {len(SEED_CUSTOMERS)} клиент, {len(SEED_ACCOUNTS)} аккаунт.")
        else:
            print(f"Деректер бұрыннан бар ({count} клиент), seed өткізіп жіберілді.")

        conn.commit()

        # 3) UNIQUE(account_number) тексеру: қайталанған нөмірді қосып көреміз
        try:
            with conn.transaction():  # ішкі SAVEPOINT, қате болса тек осы қадам қайтады
                conn.execute(
                    "INSERT INTO accounts (customer_id, account_number, balance) "
                    "VALUES ((SELECT min(customer_id) FROM customers), 'KZ0001', 0)"
                )
            print("ҚАТЕ: дубликат қабылданды (UNIQUE жұмыс істемей тұр)!")
        except errors.UniqueViolation as e:
            print("UNIQUE тексерілді: дубликат account_number қабылданбады ->", e.diag.constraint_name)


if __name__ == "__main__":
    main()