from typing import Union, TYPE_CHECKING

from bt_decode import AxonInfo, PrometheusInfo, decode_list
from scalecodec import ss58_encode
from bittensor_wallet.utils import SS58_FORMAT

from async_substrate_interface.utils import hex_to_bytes
from async_substrate_interface.types import ScaleObj

if TYPE_CHECKING:
    from async_substrate_interface.types import Runtime


def _determine_if_old_runtime_call(runtime_call_def, metadata_v15_value) -> bool:
    # Check if the output type is a Vec<u8>
    # If so, call the API using the old method
    output_type_def = [
        x
        for x in metadata_v15_value["types"]["types"]
        if x["id"] == runtime_call_def["output"]
    ]
    if output_type_def:
        output_type_def = output_type_def[0]

        if "sequence" in output_type_def["type"]["def"]:
            output_type_seq_def_id = output_type_def["type"]["def"]["sequence"]["type"]
            output_type_seq_def = [
                x
                for x in metadata_v15_value["types"]["types"]
                if x["id"] == output_type_seq_def_id
            ]
            if output_type_seq_def:
                output_type_seq_def = output_type_seq_def[0]
                if (
                    "primitive" in output_type_seq_def["type"]["def"]
                    and output_type_seq_def["type"]["def"]["primitive"] == "u8"
                ):
                    return True
    return False


def _bt_decode_to_dict_or_list(obj) -> Union[dict, list[dict]]:
    if isinstance(obj, list):
        return [_bt_decode_to_dict_or_list(item) for item in obj]

    as_dict = {}
    for key in dir(obj):
        if not key.startswith("_"):
            val = getattr(obj, key)
            if isinstance(val, (AxonInfo, PrometheusInfo)):
                as_dict[key] = _bt_decode_to_dict_or_list(val)
            else:
                as_dict[key] = val
    return as_dict


def _decode_scale_list_with_runtime(
    type_strings: list[str],
    scale_bytes_list: list[bytes],
    runtime_registry,
    return_scale_obj: bool = False,
):
    obj = decode_list(type_strings, runtime_registry, scale_bytes_list)
    if return_scale_obj:
        return [ScaleObj(x) for x in obj]
    else:
        return obj


def decode_query_map(
    result_group_changes,
    prefix,
    runtime: "Runtime",
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

    result = []
    # Determine type string
    key_type_string_ = []
    for n in range(len(params), len(param_types)):
        key_type_string_.append(f"[u8; {concat_hash_len(key_hashers[n])}]")
        key_type_string_.append(param_types[n])
    key_type_string = f"({', '.join(key_type_string_)})"

    pre_decoded_keys = []
    pre_decoded_key_types = [key_type_string] * len(result_group_changes)
    pre_decoded_values = []
    pre_decoded_value_types = [value_type] * len(result_group_changes)

    for item in result_group_changes:
        pre_decoded_keys.append(bytes.fromhex(item[0][len(prefix) :]))
        pre_decoded_values.append(hex_to_bytes_(item[1]))
    all_decoded = _decode_scale_list_with_runtime(
        pre_decoded_key_types + pre_decoded_value_types,
        pre_decoded_keys + pre_decoded_values,
        runtime.registry,
    )
    middl_index = len(all_decoded) // 2
    decoded_keys = all_decoded[:middl_index]
    decoded_values = [ScaleObj(x) for x in all_decoded[middl_index:]]
    for dk, dv in zip(decoded_keys, decoded_values):
        try:
            # strip key_hashers to use as item key
            if len(param_types) - len(params) == 1:
                item_key = dk[1]
            else:
                item_key = tuple(
                    dk[key + 1] for key in range(len(params), len(param_types) + 1, 2)
                )

        except Exception as _:
            if not ignore_decoding_errors:
                raise
            item_key = None

        item_value = dv
        result.append([item_key, item_value])
    return result
