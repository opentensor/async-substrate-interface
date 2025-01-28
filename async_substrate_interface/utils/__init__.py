import importlib


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
