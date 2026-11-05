# import os
# import psycopg
# from dotenv import load_dotenv

# load_dotenv(override=True)

# def get_conn():
#     return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3)
import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv(override=True)

# Пул қосымша іске қосылғанда БІР рет жасалады (модуль импортталғанда)
pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    min_size=2,          # 2 қосылым әрдайым ашық
    max_size=8,          # ең көбі 8
    timeout=5.0,         # бос қосылым күту уақыты (сек), содан кейін PoolTimeout
    kwargs={"connect_timeout": 3},
    open=True,
)


def get_conn():
    """Пулдан қосылым алады. `with get_conn() as conn:` ретінде қолданылады,
    блоктан шыққанда қосылым пулға қайтарылады."""
    return pool.connection()