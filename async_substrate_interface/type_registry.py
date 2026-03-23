from typing import Union
from collections import namedtuple
from bt_decode import (
    NeuronInfo,
    NeuronInfoLite,
    DelegateInfo,
    StakeInfo,
    SubnetHyperparameters,
    SubnetInfo,
    SubnetInfoV2,
    encode,
)
from scalecodec import ss58_decode


def stake_info_decode_vec_legacy_compatibility(
    item,
) -> list[dict[str, Union[str, int, bytes, bool]]]:
    stake_infos: list[StakeInfo] = StakeInfo.decode_vec(item)
    NewStakeInfo = namedtuple(
        "NewStakeInfo",
        [
            "netuid",
            "hotkey",
            "coldkey",
            "stake",
            "locked",
            "emission",
            "drain",
            "is_registered",
        ],
    )
    output = []
    for stake_info in stake_infos:
        output.append(
            NewStakeInfo(
                0,
                stake_info.hotkey,
                stake_info.coldkey,
                stake_info.stake,
                0,
                0,
                0,
                False,
            )
        )
    return output


def preprocess_get_stake_info_for_coldkeys(addrs):
    output = []
    if isinstance(addrs[0], list):  # I think
        for addr in addrs[0]:
            output.append(list(bytes.fromhex(ss58_decode(addr))))
    else:
        if isinstance(addrs[0], dict):
            for addr in addrs[0]["coldkey_accounts"]:
                output.append(list(bytes.fromhex(ss58_decode(addr))))
    return output


_TYPE_REGISTRY: dict[str, dict] = {
    "types": {
        "Balance": "u64",  # Need to override default u128
    },
    "runtime_api": {
        "DelegateInfoRuntimeApi": {
            "methods": {
                "get_delegated": {
                    "params": [
                        {
                            "name": "coldkey",
                            "type": "Vec<u8>",
                        },
                    ],
                    "encoder": lambda addr, reg: encode(
                        "Vec<u8>", reg, list(bytes.fromhex(ss58_decode(addr)))
                    ),
                    "type": "Vec<u8>",
                    "decoder": DelegateInfo.decode_delegated,
                },
                "get_delegates": {
                    "params": [],
                    "type": "Vec<u8>",
                    "decoder": DelegateInfo.decode_vec,
                },
            }
        },
        "NeuronInfoRuntimeApi": {
            "methods": {
                "get_neuron_lite": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                        {
                            "name": "uid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": NeuronInfoLite.decode,
                },
                "get_neurons_lite": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": NeuronInfoLite.decode_vec,
                },
                "get_neuron": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                        {
                            "name": "uid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": NeuronInfo.decode,
                },
                "get_neurons": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": NeuronInfo.decode_vec,
                },
            }
        },
        "StakeInfoRuntimeApi": {
            "methods": {
                "get_stake_info_for_coldkey": {
                    "params": [
                        {
                            "name": "coldkey_account_vec",
                            "type": "Vec<u8>",
                        },
                    ],
                    "type": "Vec<u8>",
                    "encoder": lambda addr, reg: encode(
                        "Vec<u8>",
                        reg,
                        list(
                            bytes.fromhex(
                                ss58_decode(
                                    addr[0]
                                    if isinstance(addr, list)
                                    else addr["coldkey_account"]
                                )
                            )
                        ),
                    ),
                    "decoder": stake_info_decode_vec_legacy_compatibility,
                },
                "get_stake_info_for_coldkeys": {
                    "params": [
                        {
                            "name": "coldkey_account_vecs",
                            "type": "Vec<Vec<u8>>",
                        },
                    ],
                    "type": "Vec<u8>",
                    "encoder": lambda addrs, reg: encode(
                        "Vec<Vec<u8>>",
                        reg,
                        preprocess_get_stake_info_for_coldkeys(addrs),
                    ),
                    "decoder": StakeInfo.decode_vec_tuple_vec,
                },
            },
        },
        "SubnetInfoRuntimeApi": {
            "methods": {
                "get_subnet_hyperparams": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": SubnetHyperparameters.decode_option,
                },
                "get_subnet_info": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": SubnetInfo.decode_option,
                },
                "get_subnet_info_v2": {
                    "params": [
                        {
                            "name": "netuid",
                            "type": "u16",
                        },
                    ],
                    "type": "Vec<u8>",
                    "decoder": SubnetInfoV2.decode_option,
                },
                "get_subnets_info": {
                    "params": [],
                    "type": "Vec<u8>",
                    "decoder": SubnetInfo.decode_vec_option,
                },
                "get_subnets_info_v2": {
                    "params": [],
                    "type": "Vec<u8>",
                    "decoder": SubnetInfo.decode_vec_option,
                },
            }
        },
    },
}
