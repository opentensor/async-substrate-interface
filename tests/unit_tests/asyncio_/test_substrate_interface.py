import asyncio
from unittest.mock import AsyncMock, MagicMock, ANY

import pytest
from websockets.exceptions import InvalidURI

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.types import ScaleObj


ARCHIVE_ENTRYPOINT = "wss://archive.chain.opentensor.ai:443"


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
        side_effect=lambda method, params, runtime: {
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
    substrate.decode_scale.assert_called_once_with(
        "scale_info::1", b"\x00", runtime=ANY
    )

    # encode_scale should not be called since no inputs
    substrate.encode_scale.assert_not_called()

    # Check RPC request called for the state_call
    substrate.rpc_request.assert_any_call(
        "state_call", ["SubstrateApi_SubstrateMethod", "", None], runtime=ANY
    )


@pytest.mark.asyncio
async def test_websocket_shutdown_timer():
    # using default ws shutdown timer of 5.0 seconds
    async with AsyncSubstrateInterface("wss://lite.sub.latent.to:443") as substrate:
        await substrate.get_chain_head()
        await asyncio.sleep(6)
        assert (
            substrate.ws._initialized is False
        )  # connection should have closed automatically

    # using custom ws shutdown timer of 10.0 seconds
    async with AsyncSubstrateInterface(
        "wss://lite.sub.latent.to:443", ws_shutdown_timer=10.0
    ) as substrate:
        await substrate.get_chain_head()
        await asyncio.sleep(6)  # same sleep time as before
        assert substrate.ws._initialized is True  # connection should still be open


@pytest.mark.asyncio
async def test_legacy_decoding():
    # roughly 4000 blocks before metadata v15 was added
    pre_metadata_v15_block = 3_010_611

    async with AsyncSubstrateInterface(ARCHIVE_ENTRYPOINT) as substrate:
        block_hash = await substrate.get_block_hash(pre_metadata_v15_block)
        events = await substrate.get_events(block_hash)
        assert isinstance(events, list)

        query_map_result = await substrate.query_map(
            module="SubtensorModule",
            storage_function="NetworksAdded",
            block_hash=block_hash,
        )
        async for key, value in query_map_result:
            assert isinstance(key, int)
            assert isinstance(value, ScaleObj)

        unix = await substrate.query(
            "Timestamp",
            "Now",
            block_hash=block_hash,
        )
        assert unix.value == 1716358476004
