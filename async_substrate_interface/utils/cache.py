import asyncio
import inspect
from collections import OrderedDict
import functools
import logging
import os
import pickle
import sqlite3
from pathlib import Path
from typing import Callable, Any, Awaitable, Hashable, Optional

USE_CACHE = True if os.getenv("NO_CACHE") != "1" else False
CACHE_LOCATION = (
    os.path.expanduser(
        os.getenv("CACHE_LOCATION", "~/.cache/async-substrate-interface")
    )
    if USE_CACHE
    else ":memory:"
)

logger = logging.getLogger("async_substrate_interface")


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
        logger.exception("Cache error", exc_info=e)
        pass


def _insert_into_cache(c, conn, table_name, key, result, chain):
    try:
        c.execute(
            f"INSERT OR REPLACE INTO {table_name} (key, value, chain) VALUES (?,?,?)",
            (key, pickle.dumps(result), chain),
        )
        conn.commit()
    except (pickle.PickleError, sqlite3.Error) as e:
        logger.exception("Cache error", exc_info=e)
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
        @cached_fetcher(max_size=maxsize)
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


class LRUCache:
    """
    Basic Least-Recently-Used Cache, with simple methods `set` and `get`
    """

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache = OrderedDict()

    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def get(self, key):
        if key in self.cache:
            # Mark as recently used
            self.cache.move_to_end(key)
            return self.cache[key]
        return None


class CachedFetcher:
    """
    Async caching class that allows the standard async LRU cache system, but also allows for concurrent
    asyncio calls (with the same args) to use the same result of a single call.

    This should only be used for asyncio calls where the result is immutable.

    Concept and usage:
        ```
        async def fetch(self, block_hash: str) -> str:
            return await some_resource(block_hash)

        a1, a2, b = await asyncio.gather(fetch("a"), fetch("a"), fetch("b"))
        ```

        Here, you are making three requests, but you really only need to make two I/O requests
        (one for "a", one for "b"), and while you wouldn't typically make a request like this directly, it's very
        common in using this library to inadvertently make these requests y gathering multiple resources that depend
        on the calls like this under the hood.

        By using

        ```
        @cached_fetcher(max_size=512)
        async def fetch(self, block_hash: str) -> str:
            return await some_resource(block_hash)

        a1, a2, b = await asyncio.gather(fetch("a"), fetch("a"), fetch("b"))
        ```

        You are only making two I/O calls, and a2 will simply use the result of a1 when it lands.
    """

    def __init__(
        self,
        max_size: int,
        method: Callable[..., Awaitable[Any]],
        cache_key_index: Optional[int] = 0,
    ):
        """
        Args:
            max_size: max size of the cache (in items)
            method: the function to cache
            cache_key_index: if the method takes multiple args, this is the index of that cache key in the args list
                (default is the first arg). By setting this to `None`, it will use all args as the cache key.
        """
        self._inflight: dict[Hashable, asyncio.Future] = {}
        self._method = method
        self._cache = LRUCache(max_size=max_size)
        self._cache_key_index = cache_key_index

    def make_cache_key(self, args: tuple, kwargs: dict) -> Hashable:
        bound = inspect.signature(self._method).bind(*args, **kwargs)
        bound.apply_defaults()

        if self._cache_key_index is not None:
            key_name = list(bound.arguments)[self._cache_key_index]
            return bound.arguments[key_name]

        return (tuple(bound.arguments.items()),)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = self.make_cache_key(args, kwargs)

        if item := self._cache.get(key):
            return item

        if key in self._inflight:
            return await self._inflight[key]

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._inflight[key] = future

        try:
            result = await self._method(*args, **kwargs)
            self._cache.set(key, result)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            self._inflight.pop(key, None)


class _CachedFetcherMethod:
    """
    Helper class for using CachedFetcher with method caches (rather than functions)
    """

    def __init__(self, method, max_size: int, cache_key_index: int):
        self.method = method
        self.max_size = max_size
        self.cache_key_index = cache_key_index
        self._instances = {}

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Cache per-instance
        if instance not in self._instances:
            bound_method = self.method.__get__(instance, owner)
            self._instances[instance] = CachedFetcher(
                max_size=self.max_size,
                method=bound_method,
                cache_key_index=self.cache_key_index,
            )
        return self._instances[instance]


def cached_fetcher(max_size: int, cache_key_index: int = 0):
    """Wrapper for CachedFetcher. See example in CachedFetcher docstring."""

    def wrapper(method):
        return _CachedFetcherMethod(method, max_size, cache_key_index)

    return wrapper
