import json
import threading
import urllib.request
import urllib.error
from collections import Counter

BASE = "http://127.0.0.1:5000"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def balances(label):
    _, text = call("GET", "/accounts?customer_id=1")
    rows = [(a["account_id"], a["balance"]) for a in json.loads(text)]
    print(label, rows)

balances("алдында:")
print("1->2, 1000:", call("POST", "/transfer", {"from_account": 1, "to_account": 2, "amount": 1000}))
balances("кейін:  ")
print("тым көп  :", call("POST", "/transfer", {"from_account": 1, "to_account": 2, "amount": 99999999}))
print("бір акк. :", call("POST", "/transfer", {"from_account": 1, "to_account": 1, "amount": 10}))
print("жоқ акк. :", call("POST", "/transfer", {"from_account": 1, "to_account": 9999, "amount": 10}))
balances("қате тесттен кейін:")

# Task 5: қарама-қарсы бағыттағы 20 бір мезгілдегі трансфер (deadlock болмауы керек)
results = Counter()
lock = threading.Lock()

def worker(a, b):
    status, _ = call("POST", "/transfer", {"from_account": a, "to_account": b, "amount": 10})
    with lock:
        results[status] += 1

threads = [threading.Thread(target=worker, args=((1, 2) if i % 2 == 0 else (2, 1))) for i in range(20)]
for t in threads: t.start()
for t in threads: t.join()

print("\nбір мезгілдегі 20 сұраныс, статус кодтары:", dict(results))
balances("соңында:")