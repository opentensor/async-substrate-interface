import asyncio
import threading
from typing import Optional


class EventLoopManager:
    """Singleton class to manage a living asyncio event loop."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_event_loop()
        return cls._instance

    def _init_event_loop(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

    def _start_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coroutine):
        while self.loop is None:
            pass
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return future.result()  # Blocks until coroutine completes

    def stop(self):
        """Stop the event loop."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    @classmethod
    def get_event_loop(cls) -> asyncio.AbstractEventLoop:
        return cls().loop


def hex_to_bytes(hex_str: str) -> bytes:
    """
    Converts a hex-encoded string into bytes. Handles 0x-prefixed and non-prefixed hex-encoded strings.
    """
    if hex_str.startswith("0x"):
        bytes_result = bytes.fromhex(hex_str[2:])
    else:
        bytes_result = bytes.fromhex(hex_str)
    return bytes_result


def event_loop_is_running() -> Optional[asyncio.AbstractEventLoop]:
    """
    Simple function to check if event loop is running. Returns the loop if it is, otherwise None.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def get_event_loop() -> asyncio.AbstractEventLoop:
    """
    If an event loop is already running, returns that. Otherwise, creates a new event loop,
        and sets it as the main event loop for this thread, returning the newly-created event loop.
    """
    if loop := event_loop_is_running():
        event_loop = loop
    else:
        event_loop = asyncio.get_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop
