import os
import psycopg
from dotenv import load_dotenv

load_dotenv()  # T2: .env файлынан оқиды

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    print(conn.execute("SELECT version()").fetchone()[0])  # T1
    print("autocommit:", conn.autocommit)                    # T3 -> False