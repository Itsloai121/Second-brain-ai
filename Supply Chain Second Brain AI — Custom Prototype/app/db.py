from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from .config import DATABASE_URL
pool=ConnectionPool(DATABASE_URL,min_size=1,max_size=8,open=False)
def open_pool(): pool.open()
def close_pool(): pool.close()
@contextmanager
def db():
    with pool.connection() as conn:
        with conn.cursor() as cur: yield cur
        conn.commit()
