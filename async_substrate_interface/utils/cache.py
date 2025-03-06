import functools
import os
import pickle
import sqlite3
import asyncstdlib as a

USE_CACHE = True if os.getenv("NO_CACHE") != "1" else False
CACHE_LOCATION = (
    os.path.expanduser(
        os.getenv("CACHE_LOCATION", "~/.cache/async-substrate-interface")
    )
    if USE_CACHE
    else ":memory:"
)


def _get_table_name(func):
    """Convert "ClassName.method_name" to "ClassName_method_name"""
    return func.__qualname__.replace(".", "_")


def _check_if_local(chain: str) -> bool:
    return any([x in chain for x in ["127.0.0.1", "localhost", "0.0.0.0"]])


def _create_table(c, conn, table_name):
    c.execute(
        f"CREATE TABLE IF NOT EXISTS {table_name} (key BLOB PRIMARY KEY, value BLOB, chain TEXT)"
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
            f"INSERT OR REPLACE INTO {table_name} VALUES (?,?,?)",
            (key, pickle.dumps(result), chain),
        )
        conn.commit()
    except (pickle.PickleError, sqlite3.Error) as e:
        print(f"Cache error: {str(e)}")
        pass


def sql_lru_cache(maxsize=None):
    def decorator(func):
        conn = sqlite3.connect(CACHE_LOCATION)
        c = conn.cursor()
        table_name = _get_table_name(func)
        _create_table(c, conn, table_name)

        @functools.lru_cache(maxsize=maxsize)
        def inner(self, *args, **kwargs):
            c = conn.cursor()
            key = pickle.dumps((args, kwargs))
            chain = self.url
            if not (local_chain := _check_if_local(chain)) or not USE_CACHE:
                result = _retrieve_from_cache(c, table_name, key, chain)
                if result is not None:
                    return result

            # If not in DB, call func and store in DB
            result = func(self, *args, **kwargs)

            if not local_chain or not USE_CACHE:
                _insert_into_cache(c, conn, table_name, key, result, chain)

            return result

        return inner

    return decorator


def async_sql_lru_cache(maxsize=None):
    def decorator(func):
        conn = sqlite3.connect(CACHE_LOCATION)
        c = conn.cursor()
        table_name = _get_table_name(func)
        _create_table(c, conn, table_name)

        @a.lru_cache(maxsize=maxsize)
        async def inner(self, *args, **kwargs):
            c = conn.cursor()
            key = pickle.dumps((args, kwargs))
            chain = self.url

            if not (local_chain := _check_if_local(chain)) or not USE_CACHE:
                result = _retrieve_from_cache(c, table_name, key, chain)
                if result is not None:
                    return result

            # If not in DB, call func and store in DB
            result = await func(self, *args, **kwargs)
            if not local_chain or not USE_CACHE:
                _insert_into_cache(c, conn, table_name, key, result, chain)

            return result

        return inner

    return decorator
