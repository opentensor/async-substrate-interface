from scalecodec import ss58_encode

from async_substrate_interface.utils import hex_to_bytes
from bt_decode import decode as decode_by_type_string, PortableRegistry
from bittensor_wallet.utils import SS58_FORMAT


class ScaleObj:
    def __init__(self, value):
        self.value = value


def _decode_scale_with_runtime(
    type_string: str,
    scale_bytes: bytes,
    runtime_registry: "Runtime",
    return_scale_obj: bool = False,
):
    if scale_bytes == b"":
        return None
    if type_string == "scale_info::0":  # Is an AccountId
        # Decode AccountId bytes to SS58 address
        return ss58_encode(scale_bytes, SS58_FORMAT)
    else:
        obj = decode_by_type_string(type_string, runtime_registry, scale_bytes)
    if return_scale_obj:
        return ScaleObj(obj)
    else:
        return obj


def decode_query_map(
    result_group_changes,
    prefix,
    runtime_registry,
    param_types,
    params,
    value_type,
    key_hashers,
    ignore_decoding_errors,
):
    def concat_hash_len(key_hasher: str) -> int:
        """
        Helper function to avoid if statements
        """
        if key_hasher == "Blake2_128Concat":
            return 16
        elif key_hasher == "Twox64Concat":
            return 8
        elif key_hasher == "Identity":
            return 0
        else:
            raise ValueError("Unsupported hash type")

    hex_to_bytes_ = hex_to_bytes
    runtime_registry = PortableRegistry.from_json(runtime_registry)

    result = []
    for item in result_group_changes:
        try:
            # Determine type string
            key_type_string = []
            for n in range(len(params), len(param_types)):
                key_type_string.append(f"[u8; {concat_hash_len(key_hashers[n])}]")
                key_type_string.append(param_types[n])

            item_key_obj = _decode_scale_with_runtime(
                f"({', '.join(key_type_string)})",
                bytes.fromhex(item[0][len(prefix) :]),
                runtime_registry,
                False,
            )

            # strip key_hashers to use as item key
            if len(param_types) - len(params) == 1:
                item_key = item_key_obj[1]
            else:
                item_key = tuple(
                    item_key_obj[key + 1]
                    for key in range(len(params), len(param_types) + 1, 2)
                )

        except Exception as _:
            if not ignore_decoding_errors:
                raise
            item_key = None

        try:
            item_bytes = hex_to_bytes_(item[1])

            item_value = _decode_scale_with_runtime(
                value_type, item_bytes, runtime_registry, True
            )

        except Exception as _:
            if not ignore_decoding_errors:
                raise
            item_value = None
        result.append([item_key, item_value])
    return result


if __name__ == "__main__":
    pass
