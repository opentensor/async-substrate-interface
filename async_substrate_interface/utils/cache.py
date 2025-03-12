import functools
import os
import pickle
import sqlite3
from pathlib import Path
import asyncstdlib as a

USE_CACHE = True if os.getenv("NO_CACHE") != "1" else False
CACHE_LOCATION = (
    os.path.expanduser(
        os.getenv("CACHE_LOCATION", "~/.cache/async-substrate-interface")
    )
    if USE_CACHE
    else ":memory:"
)


def _ensure_dir():
    path = Path(CACHE_LOCATION).parent
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def _get_table_name(func):
    """Convert "ClassName.method_name" to "ClassName_method_name"""
    return func.__qualname__.replace(".", "_")


def _check_if_local(chain: str) -> bool:
    return any([x in chain for x in ["127.0.0.1", "localhost", "0.0.0.0"]])


def _create_table(c, conn, table_name):
    c.execute(
        f"""CREATE TABLE IF NOT EXISTS {table_name} 
        (
           rowid INTEGER PRIMARY KEY AUTOINCREMENT,
           key BLOB,
           value BLOB,
           chain TEXT,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    c.execute(
        f"""CREATE TRIGGER IF NOT EXISTS prune_rows_trigger AFTER INSERT ON {table_name}
            BEGIN
              DELETE FROM {table_name}
              WHERE rowid IN (
                SELECT rowid FROM {table_name}
                ORDER BY created_at DESC
                LIMIT -1 OFFSET 500
              );
            END;"""
    )
    conn.commit()


def _retrieve_from_cache(c, table_name, key, chain):
    try:
        c.execute(
            f"SELECT value FROM {table_name} WHERE key=? AND chain=?", (key, chain)
        )
        result = c.fetchone()
        if result is not None:
            return pickle.loads(result[0])
    except (pickle.PickleError, sqlite3.Error) as e:
        print(f"Cache error: {str(e)}")
        pass


def _insert_into_cache(c, conn, table_name, key, result, chain):
    try:
        c.execute(
            f"INSERT OR REPLACE INTO {table_name} (key, value, chain) VALUES (?,?,?)",
            (key, pickle.dumps(result), chain),
        )
        conn.commit()
    except (pickle.PickleError, sqlite3.Error) as e:
        print(f"Cache error: {str(e)}")
        pass


def _shared_inner_fn_logic(func, self, args, kwargs):
    chain = self.url
    if not (local_chain := _check_if_local(chain)) or not USE_CACHE:
        _ensure_dir()
        conn = sqlite3.connect(CACHE_LOCATION)
        c = conn.cursor()
        table_name = _get_table_name(func)
        _create_table(c, conn, table_name)
        key = pickle.dumps((args, kwargs))
        result = _retrieve_from_cache(c, table_name, key, chain)
    else:
        result = None
        c = None
        conn = None
        table_name = None
        key = None
    return c, conn, table_name, key, result, chain, local_chain


def sql_lru_cache(maxsize=None):
    def decorator(func):
        @functools.lru_cache(maxsize=maxsize)
        def inner(self, *args, **kwargs):
            c, conn, table_name, key, result, chain, local_chain = (
                _shared_inner_fn_logic(func, self, args, kwargs)
            )

            # If not in DB, call func and store in DB
            result = func(self, *args, **kwargs)

            if not local_chain or not USE_CACHE:
                _insert_into_cache(c, conn, table_name, key, result, chain)

            return result

        return inner

    return decorator


def async_sql_lru_cache(maxsize=None):
    def decorator(func):
        @a.lru_cache(maxsize=maxsize)
        async def inner(self, *args, **kwargs):
            c, conn, table_name, key, result, chain, local_chain = (
                _shared_inner_fn_logic(func, self, args, kwargs)
            )

            # If not in DB, call func and store in DB
            result = await func(self, *args, **kwargs)
            if not local_chain or not USE_CACHE:
                _insert_into_cache(c, conn, table_name, key, result, chain)

            return result

        return inner

    return decorator
