from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj
from tests.helpers.settings import ARCHIVE_ENTRYPOINT


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
