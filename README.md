# KazBank Transaction API

Flask and PostgreSQL (psycopg3) REST API. CSCI2204 Database Management Systems, KBTU Fall 2026.

## Features

- Shared `ConnectionPool` (min=2, max=8), created once when the app starts.
- All queries use parameters (`%s`) to prevent SQL injection.
- `POST /transfer`: atomic, uses `SERIALIZABLE` isolation, `SAVEPOINT`, ordered locking to prevent deadlocks (smaller `account_id` first), and retry on `SerializationFailure`.
- Error handling: `UniqueViolation` → 409, `NotNullViolation` → 400, `OperationalError` → 503.

## Installation

Requirements: Python 3.10+, PostgreSQL 15+.

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

Copy `.env.example` to `.env` and add your password:

    DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/kazbank

Create the database and run setup:

    psql -U postgres -c "CREATE DATABASE kazbank;"
    python init_db.py

Run the server:

    python run.py        # http://127.0.0.1:5000

## Endpoints

| Method | URL | Description | Success Status |
|---|---|---|---|
| GET | `/customers` (`?city=Almaty`) | List all customers | 200 |
| POST | `/customers` | Add a new customer | 201 |
| GET | `/accounts?customer_id=1` | Get customer accounts | 200 |
| GET | `/transactions?account_id=1` | Get transaction history | 200 |
| POST | `/transactions` | Record debit or credit | 201 |
| POST | `/transfer` | Transfer money between accounts | 200 |
| GET | `/health` | Check pool status | 200 |

## cURL Examples

    curl http://localhost:5000/customers
    curl "http://localhost:5000/customers?city=Almaty"
    curl "http://localhost:5000/accounts?customer_id=1"
    curl "http://localhost:5000/transactions?account_id=1"

    curl -X POST http://localhost:5000/customers \
      -H "Content-Type: application/json" \
      -d '{"full_name": "Test User", "city": "Almaty", "email": "test@example.kz"}'

    curl -X POST http://localhost:5000/transactions \
      -H "Content-Type: application/json" \
      -d '{"account_id": 1, "amount": 1000, "tx_type": "credit"}'

    curl -X POST http://localhost:5000/transfer \
      -H "Content-Type: application/json" \
      -d '{"from_account": 1, "to_account": 2, "amount": 500}'

    curl http://localhost:5000/health

*Note for Windows PowerShell:* JSON quotes can cause issues. Use `curl.exe ... --data "@body.json"` with a JSON file instead.

## Error Codes

| Code | When it happens |
|---|---|
| 400 | Bad input (missing fields, wrong type, low balance, same accounts) |
| 404 | Account not found |
| 409 | Duplicate email / Concurrent update (retries failed) |
| 503 | Database is down |

## Testing

    python test_api.py        # Test endpoints and SQL injection
    python test_transfer.py   # Test transfers and 20 parallel requests
    python load_test.py       # Test connection pool reuse