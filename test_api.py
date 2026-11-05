import json
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://127.0.0.1:5000"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def q(text):
    return urllib.parse.quote(text)

tests = [
    ("credit 1000 (күтілетіні 201)", "POST", "/transactions",
     {"account_id": 1, "amount": 1000, "tx_type": "credit"}),
    ("debit 1000 (күтілетіні 201)", "POST", "/transactions",
     {"account_id": 1, "amount": 1000, "tx_type": "debit"}),
    ("debit тым көп (күтілетіні 400)", "POST", "/transactions",
     {"account_id": 1, "amount": 99999999, "tx_type": "debit"}),
    ("жоқ аккаунт (күтілетіні 404)", "POST", "/transactions",
     {"account_id": 9999, "amount": 100, "tx_type": "credit"}),
    ("қате tx_type (күтілетіні 400)", "POST", "/transactions",
     {"account_id": 1, "amount": 100, "tx_type": "hack"}),
    ("тарих (күтілетіні 200)", "GET", "/transactions?account_id=1", None),
    ("SQL injection: OR (күтілетіні 200 және [])", "GET",
     "/customers?city=" + q("Almaty' OR '1'='1"), None),
    ("SQL injection: DROP (күтілетіні 200 және [])", "GET",
     "/customers?city=" + q("x'; DROP TABLE customers; --"), None),
    ("customers әлі бар (күтілетіні 200)", "GET", "/customers", None),
]

for name, method, path, body in tests:
    status, text = call(method, path, body)
    print(f"{name}\n  -> {status} {' '.join(text.split())[:150]}\n")