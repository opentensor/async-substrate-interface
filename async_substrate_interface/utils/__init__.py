import importlib
from itertools import cycle
import random
import string

id_cycle = cycle(range(1, 999))

rng = random.Random()


def get_next_id() -> str:
    """
    Generates a pseudo-random ID by returning the next int of a range from 1-998 prepended with
    two random ascii characters.
    """
    random_letters = "".join(rng.choices(string.ascii_letters, k=2))
    return f"{random_letters}{next(id_cycle)}"


def hex_to_bytes(hex_str: str) -> bytes:
    """
    Converts a hex-encoded string into bytes. Handles 0x-prefixed and non-prefixed hex-encoded strings.
    """
    if hex_str.startswith("0x"):
        bytes_result = bytes.fromhex(hex_str[2:])
    else:
        bytes_result = bytes.fromhex(hex_str)
    return bytes_result


def import_json_lib():
    libs = ["ujson", "orjson", "simplejson", "json"]

    for lib in libs:
        try:
            return importlib.import_module(lib)
        except ImportError:
            continue

    raise ImportError("None of the specified JSON libraries are installed.")


json = import_json_lib()
