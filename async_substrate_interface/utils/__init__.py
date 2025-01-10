import asyncio
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Coroutine


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


def execute_coroutine(
    coroutine: "Coroutine", event_loop: asyncio.AbstractEventLoop = None
):
    """
    Helper function to run an asyncio coroutine synchronously.

    Args:
        coroutine (Coroutine): The coroutine to run.
        event_loop (AbstractEventLoop): The event loop to use. If `None`, attempts to fetch the already-running
            loop. If one is not running, a new loop is created.

    Returns:
        The result of the coroutine execution.
    """
    if event_loop:
        event_loop = event_loop
    else:
        event_loop = get_event_loop()
    return event_loop.run_until_complete(asyncio.wait_for(coroutine, timeout=None))
