import pytest

from async_substrate_interface.async_substrate import (
    DiskCachedAsyncSubstrateInterface,
    AsyncSubstrateInterface,
)
from async_substrate_interface.sync_substrate import SubstrateInterface


@pytest.mark.asyncio
async def test_disk_cache():
    print("Testing test_disk_cache")
    entrypoint = "wss://entrypoint-finney.opentensor.ai:443"
    async with DiskCachedAsyncSubstrateInterface(entrypoint) as disk_cached_substrate:
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
    async with AsyncSubstrateInterface(entrypoint) as non_cache_substrate:
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
    with SubstrateInterface(entrypoint) as sync_substrate:
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
    print("test_disk_cache succeeded")
