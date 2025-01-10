import asyncio
from hashlib import blake2b
from typing import Optional, TYPE_CHECKING

import base58

if TYPE_CHECKING:
    from typing import Coroutine


def ss58_decode(address: str, valid_ss58_format: Optional[int] = None) -> str:
    """
    Decodes given SS58 encoded address to an account ID

    Args:
        address: e.g. EaG2CRhJWPb7qmdcJvy3LiWdh26Jreu9Dx6R1rXxPmYXoDk
        valid_ss58_format: the format for what is considered valid

    Returns:
        Decoded string AccountId
    """

    # Check if address is already decoded
    if address.startswith("0x"):
        return address

    if address == "":
        raise ValueError("Empty address provided")

    checksum_prefix = b"SS58PRE"

    address_decoded = base58.b58decode(address)

    if address_decoded[0] & 0b0100_0000:
        ss58_format_length = 2
        ss58_format = (
            ((address_decoded[0] & 0b0011_1111) << 2)
            | (address_decoded[1] >> 6)
            | ((address_decoded[1] & 0b0011_1111) << 8)
        )
    else:
        ss58_format_length = 1
        ss58_format = address_decoded[0]

    if ss58_format in [46, 47]:
        raise ValueError(f"{ss58_format} is a reserved SS58 format")

    if valid_ss58_format is not None and ss58_format != valid_ss58_format:
        raise ValueError("Invalid SS58 format")

    # Determine checksum length according to length of address string
    if len(address_decoded) in [3, 4, 6, 10]:
        checksum_length = 1
    elif len(address_decoded) in [
        5,
        7,
        11,
        34 + ss58_format_length,
        35 + ss58_format_length,
    ]:
        checksum_length = 2
    elif len(address_decoded) in [8, 12]:
        checksum_length = 3
    elif len(address_decoded) in [9, 13]:
        checksum_length = 4
    elif len(address_decoded) in [14]:
        checksum_length = 5
    elif len(address_decoded) in [15]:
        checksum_length = 6
    elif len(address_decoded) in [16]:
        checksum_length = 7
    elif len(address_decoded) in [17]:
        checksum_length = 8
    else:
        raise ValueError("Invalid address length")

    checksum = blake2b(checksum_prefix + address_decoded[0:-checksum_length]).digest()

    if checksum[0:checksum_length] != address_decoded[-checksum_length:]:
        raise ValueError("Invalid checksum")

    return address_decoded[
        ss58_format_length : len(address_decoded) - checksum_length
    ].hex()


def _is_valid_ss58_address(value: str, valid_ss58_format: Optional[int] = None) -> bool:
    """
    Checks if given value is a valid SS58 formatted address, optionally check if address is valid for specified
    ss58_format

    Args:
        value: value to checked
        valid_ss58_format: if valid_ss58_format is provided the address must be valid for specified ss58_format
            (network) as well

    Returns:
        bool result
    """

    # Return False in case a public key is provided
    if value.startswith("0x"):
        return False

    try:
        ss58_decode(value, valid_ss58_format=valid_ss58_format)
    except ValueError:
        return False

    return True


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
