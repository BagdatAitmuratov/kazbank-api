import json
import threading
import time
import urllib.request
from collections import Counter

BASE = "http://localhost:5000"
N = 20


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return r.status, json.loads(r.read())


results = []
lock = threading.Lock()


def worker():
    t0 = time.time()
    try:
        status, _ = get("/customers")
    except Exception as e:
        status = f"ERR {e}"
    with lock:
        results.append((status, time.time() - t0))


before = get("/health")[1]["pool"]

threads = [threading.Thread(target=worker) for _ in range(N)]
start = time.time()
for t in threads:
    t.start()
for t in threads:
    t.join()
total = time.time() - start

after = get("/health")[1]["pool"]

print(f"{N} параллель сұраныс, статус кодтары:", dict(Counter(s for s, _ in results)))
print(f"Жалпы уақыт: {total:.2f} с, орташа сұраныс: "
      f"{sum(d for _, d in results) / len(results) * 1000:.0f} мс")
print()
def stat(d, key):
    return d.get(key, 0)


print("Пул статистикасы:")
print(f"  pool_size (қазір ашық қосылым): {stat(before, 'pool_size')} -> {stat(after, 'pool_size')}  (max {stat(after, 'pool_max')})")
print(f"  requests_num (пулдан алынған қосылым): +{stat(after, 'requests_num') - stat(before, 'requests_num')}")
print(f"  connections_num (жаңа қосылым ашылды): +{stat(after, 'connections_num') - stat(before, 'connections_num')}")
print(f"  requests_waiting: {stat(after, 'requests_waiting')}")