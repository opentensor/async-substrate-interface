import asyncio
import os
import time

import bittensor as bt
from bittensor.core.chain_data import decode_account_id
from bittensor.core.settings import SS58_FORMAT
import pytest
import substrateinterface

from async_substrate_interface.async_substrate import AsyncSubstrateInterface

try:
    n = int(os.getenv("NUMBER_RUNS"))
except TypeError:
    n = 3


coldkey = "5HHHHHzgLnYRvnKkHd45cRUDMHXTSwx7MjUzxBrKbY4JfZWn"

# dtao epoch is 4920350

b_pre = 4920340
b_post = 4920360


@pytest.mark.asyncio
async def test_async():
    async with bt.async_subtensor("archive") as st:
        print("ss58 format:", st.substrate.ss58_format)
        print("current block (async):", await st.block)
        for i in range(n):
            s0 = await st.get_stake_for_coldkey(coldkey, block=b_post + i)
            print(f"at block {b_post + i}: {s0}")
        for i in range(n):
            s1 = (
                await st.query_subtensor(
                    "TotalColdkeyStake", block=b_pre + i, params=[coldkey]
                )
            ).value
            print(f"at block {b_pre + i}: {s1}")
        for i in range(n):
            s2 = await st.get_stake_for_coldkey(coldkey, block=b_post + i)
            print(f"at block {b_post + i}: {s2}")


def test_sync():
    with bt.subtensor("archive") as st:
        print("ss58 format:", st.substrate.ss58_format)
        print("current block (sync):", st.block)
        for i in range(n):
            s0 = st.get_stake_for_coldkey(coldkey, block=b_post + i)
            print(f"at block {b_post + i}: {s0}")
        for i in range(n):
            s1 = st.query_subtensor("TotalColdkeyStake", b_pre + i, [coldkey]).value
            print(f"at block {b_pre + i}: {s1}")
        for i in range(n):
            s2 = st.get_stake_for_coldkey(coldkey, block=b_post + i)
            print(f"at block {b_post + i}: {s2}")


@pytest.mark.asyncio
async def test_query_map():
    async def async_gathering():
        async def exhaust(qmr):
            r = []
            async for k, v in await qmr:
                r.append((k, v))
            return r

        start = time.time()
        async with AsyncSubstrateInterface(
            "wss://entrypoint-finney.opentensor.ai:443", ss58_format=SS58_FORMAT
        ) as substrate:
            block_hash = await substrate.get_chain_head()
            tasks = [
                substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    [netuid],
                    block_hash=block_hash,
                )
                for netuid in range(1, 51)
            ]
            tasks = [exhaust(task) for task in tasks]
            print(time.time() - start)
            results_dicts_list = []
            for future in asyncio.as_completed(tasks):
                result = await future
                results_dicts_list.extend(
                    [(decode_account_id(k), v.value) for k, v in result]
                )

        elapsed = time.time() - start
        print(f"time elapsed: {elapsed}")

        print("Async Results", len(results_dicts_list))
        return results_dicts_list, block_hash

    def sync_old_method(block_hash):
        results_dicts_list = []
        start = time.time()
        substrate = substrateinterface.SubstrateInterface(
            "wss://entrypoint-finney.opentensor.ai:443"
        )
        for netuid in range(1, 51):
            tao_divs = list(
                substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    [netuid],
                    block_hash=block_hash,
                )
            )
            tao_divs = [(k.value, v.value) for k, v in tao_divs]
            results_dicts_list.extend(tao_divs)
        print(time.time() - start)
        print("Sync Results", len(results_dicts_list))
        return results_dicts_list

    async_, block_hash_ = await async_gathering()
    sync_ = sync_old_method(block_hash_)
    for k_v in async_:
        assert k_v in sync_
