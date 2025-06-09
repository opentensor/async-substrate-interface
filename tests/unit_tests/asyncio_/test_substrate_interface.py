from unittest.mock import AsyncMock, MagicMock

import pytest
from websockets.exceptions import InvalidURI

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.types import ScaleObj


@pytest.mark.asyncio
async def test_invalid_url_raises_exception():
    """Test that invalid URI raises an InvalidURI exception."""
    async_substrate = AsyncSubstrateInterface("non_existent_entry_point")
    with pytest.raises(InvalidURI):
        await async_substrate.initialize()

    with pytest.raises(InvalidURI):
        async with AsyncSubstrateInterface(
            "non_existent_entry_point"
        ) as async_substrate:
            pass


@pytest.mark.asyncio
async def test_runtime_call(monkeypatch):
    substrate = AsyncSubstrateInterface("ws://localhost", _mock=True)

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
    substrate.init_runtime = AsyncMock(return_value=fake_runtime)

    # Patch encode_scale (should not be called in this test since no inputs)
    substrate.encode_scale = AsyncMock()

    # Patch decode_scale to produce a dummy value
    substrate.decode_scale = AsyncMock(return_value="decoded_result")

    # Patch RPC request with correct behavior
    substrate.rpc_request = AsyncMock(
        side_effect=lambda method, params: {
            "result": "0x00" if method == "state_call" else {"parentHash": "0xDEADBEEF"}
        }
    )

    # Patch get_block_runtime_info
    substrate.get_block_runtime_info = AsyncMock(return_value={"specVersion": "1"})

    # Run the call
    result = await substrate.runtime_call(
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
