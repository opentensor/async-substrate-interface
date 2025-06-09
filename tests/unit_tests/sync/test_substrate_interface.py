from unittest.mock import MagicMock

from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj


def test_runtime_call(monkeypatch):
    substrate = SubstrateInterface("ws://localhost", _mock=True)
    fake_runtime = MagicMock()
    fake_metadata_v15 = MagicMock()
    fake_metadata_v15.value.return_value = {
        "apis": [
            {
                "name": "SubstrateApi",
                "methods": [
                    {
                        "name": "SubstrateMethod",
                        "inputs": [],
                        "output": "1",
                    },
                ],
            },
        ],
        "types": {
            "types": [
                {
                    "id": "1",
                    "type": {
                        "path": ["Vec"],
                        "def": {"sequence": {"type": "4"}},
                    },
                },
            ]
        },
    }
    fake_runtime.metadata_v15 = fake_metadata_v15
    substrate.init_runtime = MagicMock(return_value=fake_runtime)

    # Patch encode_scale (should not be called in this test since no inputs)
    substrate.encode_scale = MagicMock()

    # Patch decode_scale to produce a dummy value
    substrate.decode_scale = MagicMock(return_value="decoded_result")

    # Patch RPC request with correct behavior
    substrate.rpc_request = MagicMock(
        side_effect=lambda method, params: {
            "result": "0x00" if method == "state_call" else {"parentHash": "0xDEADBEEF"}
        }
    )

    # Patch get_block_runtime_info
    substrate.get_block_runtime_info = MagicMock(return_value={"specVersion": "1"})

    # Run the call
    result = substrate.runtime_call(
        "SubstrateApi",
        "SubstrateMethod",
    )

    # Validate the result is wrapped in ScaleObj
    assert isinstance(result, ScaleObj)
    assert result.value == "decoded_result"

    # Check decode_scale called correctly
    substrate.decode_scale.assert_called_once_with("scale_info::1", b"\x00")

    # encode_scale should not be called since no inputs
    substrate.encode_scale.assert_not_called()

    # Check RPC request called for the state_call
    substrate.rpc_request.assert_any_call(
        "state_call", ["SubstrateApi_SubstrateMethod", "", None]
    )
