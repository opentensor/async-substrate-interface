import pytest
import time
from async_substrate_interface.async_substrate import (
    DiskCachedAsyncSubstrateInterface,
    AsyncSubstrateInterface,
)
from async_substrate_interface.sync_substrate import SubstrateInterface
from tests.helpers.settings import LATENT_LITE_ENTRYPOINT


@pytest.mark.asyncio
async def test_disk_cache():
    print("Testing test_disk_cache")
    async with DiskCachedAsyncSubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as disk_cached_substrate:
        current_block = await disk_cached_substrate.get_block_number(None)
        block_hash = await disk_cached_substrate.get_block_hash(current_block)
        parent_block_hash = await disk_cached_substrate.get_parent_block_hash(
            block_hash
        )
        block_runtime_info = await disk_cached_substrate.get_block_runtime_info(
            block_hash
        )
        block_runtime_version_for = (
            await disk_cached_substrate.get_block_runtime_version_for(block_hash)
        )
        block_hash_from_cache = await disk_cached_substrate.get_block_hash(
            current_block
        )
        parent_block_hash_from_cache = (
            await disk_cached_substrate.get_parent_block_hash(block_hash_from_cache)
        )
        block_runtime_info_from_cache = (
            await disk_cached_substrate.get_block_runtime_info(block_hash_from_cache)
        )
        block_runtime_version_from_cache = (
            await disk_cached_substrate.get_block_runtime_version_for(
                block_hash_from_cache
            )
        )
    assert block_hash == block_hash_from_cache
    assert parent_block_hash == parent_block_hash_from_cache
    assert block_runtime_info == block_runtime_info_from_cache
    assert block_runtime_version_for == block_runtime_version_from_cache
    # Verify data integrity with non-disk cached Async Substrate Interface
    async with AsyncSubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as non_cache_substrate:
        block_hash_non_cache = await non_cache_substrate.get_block_hash(current_block)
        parent_block_hash_non_cache = await non_cache_substrate.get_parent_block_hash(
            block_hash_non_cache
        )
        block_runtime_info_non_cache = await non_cache_substrate.get_block_runtime_info(
            block_hash_non_cache
        )
        block_runtime_version_for_non_cache = (
            await non_cache_substrate.get_block_runtime_version_for(
                block_hash_non_cache
            )
        )
    assert block_hash == block_hash_non_cache
    assert parent_block_hash == parent_block_hash_non_cache
    assert block_runtime_info == block_runtime_info_non_cache
    assert block_runtime_version_for == block_runtime_version_for_non_cache
    # Verify data integrity with sync Substrate Interface
    with SubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as sync_substrate:
        block_hash_sync = sync_substrate.get_block_hash(current_block)
        parent_block_hash_sync = sync_substrate.get_parent_block_hash(
            block_hash_non_cache
        )
        block_runtime_info_sync = sync_substrate.get_block_runtime_info(
            block_hash_non_cache
        )
        block_runtime_version_for_sync = sync_substrate.get_block_runtime_version_for(
            block_hash_non_cache
        )
    assert block_hash == block_hash_sync
    assert parent_block_hash == parent_block_hash_sync
    assert block_runtime_info == block_runtime_info_sync
    assert block_runtime_version_for == block_runtime_version_for_sync
    # Verify data is pulling from disk cache
    async with DiskCachedAsyncSubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as disk_cached_substrate:
        start = time.monotonic()
        new_block_hash = await disk_cached_substrate.get_block_hash(current_block)
        new_time = time.monotonic()
        assert new_time - start < 0.001

        start = time.monotonic()
        new_parent_block_hash = await disk_cached_substrate.get_parent_block_hash(
            block_hash
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_block_runtime_info = await disk_cached_substrate.get_block_runtime_info(
            block_hash
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_block_runtime_version_for = (
            await disk_cached_substrate.get_block_runtime_version_for(block_hash)
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_block_hash_from_cache = await disk_cached_substrate.get_block_hash(
            current_block
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_parent_block_hash_from_cache = (
            await disk_cached_substrate.get_parent_block_hash(block_hash_from_cache)
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_block_runtime_info_from_cache = (
            await disk_cached_substrate.get_block_runtime_info(block_hash_from_cache)
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
        start = time.monotonic()
        new_block_runtime_version_from_cache = (
            await disk_cached_substrate.get_block_runtime_version_for(
                block_hash_from_cache
            )
        )
        new_time = time.monotonic()
        assert new_time - start < 0.001
    print("Disk Cache tests passed")
