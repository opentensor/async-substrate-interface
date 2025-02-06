from bt_decode import AxonInfo, PrometheusInfo


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


def _bt_decode_to_dict_or_list(obj) -> dict | list[dict]:
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
