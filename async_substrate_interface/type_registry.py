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
from scalecodec import ss58_encode

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
                    "encoder": lambda addr: encode(ss58_encode(addr), "Vec<u8>"),
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
                    "encoder": lambda addr: encode(ss58_encode(addr), "Vec<u8>"),
                    "decoder": StakeInfo.decode_vec,
                },
                "get_stake_info_for_coldkeys": {
                    "params": [
                        {
                            "name": "coldkey_account_vecs",
                            "type": "Vec<Vec<u8>>",
                        },
                    ],
                    "type": "Vec<u8>",
                    "encoder": lambda addrs: encode(
                        [ss58_encode(addr) for addr in addrs], "Vec<Vec<u8>>"
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
