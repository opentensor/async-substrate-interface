from unittest.mock import MagicMock

from scalecodec import ss58_encode

from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj

from tests.helpers.settings import ARCHIVE_ENTRYPOINT, LATENT_LITE_ENTRYPOINT


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
    substrate.close()


def test_legacy_decoding():
    # roughly 4000 blocks before metadata v15 was added
    pre_metadata_v15_block = 3_010_611

    with SubstrateInterface(ARCHIVE_ENTRYPOINT) as substrate:
        block_hash = substrate.get_block_hash(pre_metadata_v15_block)
        events = substrate.get_events(block_hash)
        assert isinstance(events, list)

        query_map_result = substrate.query_map(
            module="SubtensorModule",
            storage_function="NetworksAdded",
            block_hash=block_hash,
        )
        for key, value in query_map_result:
            assert isinstance(key, int)
            assert isinstance(value, ScaleObj)

        timestamp = substrate.query(
            "Timestamp",
            "Now",
            block_hash=block_hash,
        )
        assert timestamp.value == 1716358476004


def test_ss58_conversion():
    with SubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, decode_ss58=False
    ) as substrate:
        block_hash = substrate.get_chain_finalised_head()
        qm = substrate.query_map(
            "SubtensorModule",
            "OwnedHotkeys",
            block_hash=block_hash,
        )
        # only do the first page, bc otherwise this will be massive
        for key, value in qm.records:
            assert isinstance(key, tuple)
            assert isinstance(value, ScaleObj)
            assert isinstance(value.value, list)
            assert len(key) == 1
            for key_tuple in value.value:
                assert len(key_tuple[0]) == 32
                random_key = key_tuple[0]

        ss58_of_key = ss58_encode(bytes(random_key), substrate.ss58_format)
        assert isinstance(ss58_of_key, str)

        substrate.decode_ss58 = True  # change to decoding True

        qm = substrate.query_map(
            "SubtensorModule",
            "OwnedHotkeys",
            block_hash=block_hash,
        )
        for key, value in qm.records:
            assert isinstance(key, str)
            assert isinstance(value, ScaleObj)
            assert isinstance(value.value, list)
            if len(value.value) > 0:
                for decoded_key in value.value:
                    assert isinstance(decoded_key, str)
