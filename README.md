# KazBank Transaction API

Flask + PostgreSQL (psycopg3) REST API. CSCI2204 Database Management Systems, KBTU Fall 2026.

## Мүмкіндіктері

- Shared `ConnectionPool` (min=2, max=8), пул қосымша іске қосылғанда бір рет жасалады
- Барлық сұраныс параметрленген (`%s`), SQL injection-нан қорғалған
- `POST /transfer`: атомарлы, `SERIALIZABLE`, `SAVEPOINT`, deadlock-қа қарсы тәртіпті құлыптау (кіші `account_id` бірінші) және `SerializationFailure` кезінде retry
- Қателер: `UniqueViolation` → 409, `NotNullViolation` → 400, `OperationalError` → 503

## Орнату

Қажет: Python 3.10+, PostgreSQL 15+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` файлын `.env` деп көшіріп, құпия сөзді жаз:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/kazbank
```

Базаны жаса және схеманы толтыр:

```bash
psql -U postgres -c "CREATE DATABASE kazbank;"
python init_db.py
```

Серверді іске қос:

```bash
python run.py        # http://127.0.0.1:5000
```

## Эндпоинттер

| Method | URL | Сипаттама | Сәтті |
|---|---|---|---|
| GET | `/customers` (`?city=Almaty`) | Клиенттер тізімі | 200 |
| POST | `/customers` | Клиент қосу | 201 |
| GET | `/accounts?customer_id=1` | Клиент аккаунттары | 200 |
| GET | `/transactions?account_id=1` | Аккаунт тарихы | 200 |
| POST | `/transactions` | debit/credit жазу | 201 |
| POST | `/transfer` | Аккаунттар арасындағы аударым | 200 |
| GET | `/health` | Пул статистикасы | 200 |

## curl мысалдары

```bash
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
```

Windows PowerShell-де JSON тырнақшалары дұрыс өтпейді. JSON-ды файлға жазып, `curl.exe ... --data "@body.json"` қолдан.

## Қате кодтары

| Код | Қашан |
|---|---|
| 400 | Қате енгізу (өріс жоқ, қате `tx_type`, жеткіліксіз қаражат, бірдей аккаунттар) |
| 404 | Аккаунт табылмады |
| 409 | Қайталанған email / `Concurrent update` (retry таусылғанда) |
| 503 | Дерекқор қолжетімсіз |

## Тестілеу

```bash
python test_api.py        # endpoint-тер және SQL injection
python test_transfer.py   # аударым және 20 параллель сұраныс
python load_test.py       # пулдың қайта қолданылуы
```