import unittest.mock

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
    monkeypatch.setattr(
        "async_substrate_interface.async_substrate.Websocket", unittest.mock.Mock()
    )

    substrate = AsyncSubstrateInterface("ws://localhost")
    substrate._metadata = unittest.mock.Mock()
    substrate.metadata_v15 = unittest.mock.Mock(
        **{
            "value.return_value": {
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
            },
        }
    )
    substrate.rpc_request = unittest.mock.AsyncMock(
        return_value={
            "result": "0x00",
        },
    )
    substrate.decode_scale = unittest.mock.AsyncMock()

    result = await substrate.runtime_call(
        "SubstrateApi",
        "SubstrateMethod",
    )

    assert isinstance(result, ScaleObj)
    assert result.value is substrate.decode_scale.return_value

    substrate.rpc_request.assert_called_once_with(
        "state_call",
        ["SubstrateApi_SubstrateMethod", "", None],
    )
    substrate.decode_scale.assert_called_once_with("scale_info::1", b"\x00")
