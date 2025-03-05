import os
import bittensor as bt
import pytest

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
