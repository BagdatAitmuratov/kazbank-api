import json, random, urllib.request, urllib.error

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

email = f"test{random.randint(1000, 9999)}@kbtu.kz"
print("жаңа клиент (күтілетіні 201):  ", call("POST", "/customers", {"full_name": "Test User", "email": email}))
print("қайталанған email (күтілетіні 409):", call("POST", "/customers", {"full_name": "Test User", "email": email}))
print("full_name жоқ (күтілетіні 400):  ", call("POST", "/customers", {"email": "x" + email}))