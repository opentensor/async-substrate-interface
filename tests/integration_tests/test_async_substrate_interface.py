import time

import pytest
from scalecodec import ss58_encode

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.types import ScaleObj
from tests.helpers.settings import ARCHIVE_ENTRYPOINT, LATENT_LITE_ENTRYPOINT


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


@pytest.mark.asyncio
async def test_ss58_conversion():
    async with AsyncSubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, decode_ss58=False
    ) as substrate:
        block_hash = await substrate.get_chain_finalised_head()
        qm = await substrate.query_map(
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

        qm = await substrate.query_map(
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


@pytest.mark.asyncio
async def test_fully_exhaust_query_map():
    async with AsyncSubstrateInterface(LATENT_LITE_ENTRYPOINT) as substrate:
        block_hash = await substrate.get_chain_finalised_head()
        non_fully_exhauster_start = time.time()
        non_fully_exhausted_qm = await substrate.query_map(
            "SubtensorModule",
            "CRV3WeightCommits",
            block_hash=block_hash,
        )
        initial_records_count = len(non_fully_exhausted_qm.records)
        assert initial_records_count <= 100  # default page size
        exhausted_records_count = 0
        async for _ in non_fully_exhausted_qm:
            exhausted_records_count += 1
        non_fully_exhausted_time = time.time() - non_fully_exhauster_start

        assert len(non_fully_exhausted_qm.records) >= initial_records_count
        fully_exhausted_start = time.time()
        fully_exhausted_qm = await substrate.query_map(
            "SubtensorModule",
            "CRV3WeightCommits",
            block_hash=block_hash,
            fully_exhaust=True,
        )

        fully_exhausted_time = time.time() - fully_exhausted_start
        initial_records_count_fully_exhaust = len(fully_exhausted_qm.records)
        assert fully_exhausted_time <= non_fully_exhausted_time, (
            f"Fully exhausted took longer than non-fully exhausted with "
            f"{len(non_fully_exhausted_qm.records)} records in non-fully exhausted "
            f"in {non_fully_exhausted_time} seconds, and {initial_records_count_fully_exhaust} in fully exhausted"
            f" in {fully_exhausted_time} seconds. This could be caused by the fact that on this specific block, "
            f"there are fewer records than take up a single page. This difference should still be small."
        )
        fully_exhausted_records_count = 0
        async for _ in fully_exhausted_qm:
            fully_exhausted_records_count += 1
        assert fully_exhausted_records_count == initial_records_count_fully_exhaust
        assert initial_records_count_fully_exhaust == exhausted_records_count
