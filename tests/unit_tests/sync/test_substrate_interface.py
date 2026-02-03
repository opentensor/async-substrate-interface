import tracemalloc
from unittest.mock import MagicMock

from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj

from tests.helpers.settings import ARCHIVE_ENTRYPOINT, LATENT_LITE_ENTRYPOINT


def test_runtime_call(monkeypatch):
    print("Testing test_runtime_call")
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
    print("test_runtime_call succeeded")


def test_runtime_switching():
    print("Testing test_runtime_switching")
    block = 6067945  # block where a runtime switch happens
    with SubstrateInterface(
        ARCHIVE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as substrate:
        # assures we switch between the runtimes without error
        assert substrate.get_extrinsics(block_number=block - 20) is not None
        assert substrate.get_extrinsics(block_number=block) is not None
        assert substrate.get_extrinsics(block_number=block - 21) is not None
    print("test_runtime_switching succeeded")


def test_memory_leak():
    tracemalloc.start()
    two_mb = 2 * 1024 * 1024

    # Warmup: populate caches before taking baseline
    for _ in range(2):
        subtensor = SubstrateInterface(LATENT_LITE_ENTRYPOINT)
        subtensor.close()

    baseline_snapshot = tracemalloc.take_snapshot()

    for i in range(5):
        subtensor = SubstrateInterface(LATENT_LITE_ENTRYPOINT)
        subtensor.close()

        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.compare_to(baseline_snapshot, "lineno")
        total_diff = sum(stat.size_diff for stat in stats)
        current, peak = tracemalloc.get_traced_memory()
        # Allow cumulative growth up to 2MB per iteration from baseline
        assert total_diff < two_mb * (i + 1), (
            f"Loop {i}: diff={total_diff / 1024:.2f} KiB, current={current / 1024:.2f} KiB, "
            f"peak={peak / 1024:.2f} KiB"
        )
