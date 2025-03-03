import os
import asyncio
import bittensor as bt

use_async = (os.getenv("USE_ASYNC") == "1") or False
try:
    n = int(os.getenv("NUMBER_RUNS"))
except TypeError:
    n = 3


coldkey = "5HHHHHzgLnYRvnKkHd45cRUDMHXTSwx7MjUzxBrKbY4JfZWn"

# dtao epoch is 4920350

b_pre = 4920340
b_post = 4920360

if use_async:
    st = bt.async_subtensor(network="local")

    async def main():
        async with st:
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

    asyncio.run(main())
else:
    st = bt.subtensor(network="local")
    print("ss58 format:", st.substrate.ss58_format)
    print("current block (sync):", st.block)
    st = bt.subtensor(network="local")
    for i in range(n):
        s0 = st.get_stake_for_coldkey(coldkey, block=b_post + i)
        print(f"at block {b_post + i}: {s0}")
    for i in range(n):
        s1 = st.query_subtensor("TotalColdkeyStake", b_pre + i, [coldkey]).value
        print(f"at block {b_pre + i}: {s1}")
    for i in range(n):
        s2 = st.get_stake_for_coldkey(coldkey, block=b_post + i)
        print(f"at block {b_post + i}: {s2}")
