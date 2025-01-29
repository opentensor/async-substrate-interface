import unittest.mock

from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj


def test_runtime_call(monkeypatch):
    monkeypatch.setattr(
        "async_substrate_interface.sync_substrate.connect", unittest.mock.MagicMock()
    )

    substrate = SubstrateInterface(
        "ws://localhost",
        _mock=True,
    )
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
    substrate.rpc_request = unittest.mock.Mock(
        return_value={
            "result": "0x00",
        },
    )
    substrate.decode_scale = unittest.mock.Mock()

    result = substrate.runtime_call(
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
