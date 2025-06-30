import pytest

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.types import ScaleObj
from tests.helpers.settings import ARCHIVE_ENTRYPOINT


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

        timestamp = await substrate.query(
            "Timestamp",
            "Now",
            block_hash=block_hash,
        )
        assert timestamp.value == 1716358476004
