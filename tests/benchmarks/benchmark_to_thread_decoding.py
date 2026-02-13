"""
Results:

93 items

original (not threading) decoding:
median 3.9731219584937207
mean 3.810443129093619
stdev 0.9819147187144933

to_thread decoding:
median 2.72423210402485
mean 2.787995279103052
stdev 0.20955198981795337

"""

import asyncio

from scalecodec import ss58_encode

from async_substrate_interface.async_substrate import (
    AsyncSubstrateInterface,
    AsyncQueryMapResult,
)
from tests.helpers.settings import LATENT_LITE_ENTRYPOINT


async def benchmark_to_thread_decoding():
    async def _query_alpha(hk_: str, sem: asyncio.Semaphore) -> list:
        try:
            async with sem:
                results = []
                qm: AsyncQueryMapResult = await substrate.query_map(
                    "SubtensorModule",
                    "Alpha",
                    params=[hk_],
                    block_hash=block_hash,
                    fully_exhaust=False,
                    page_size=100,
                )
                async for result in qm:
                    results.append(result)
                return results
        except Exception as e:
            raise type(e)(f"[hotkey={hk_}] {e}") from e

    loop = asyncio.get_running_loop()
    async with AsyncSubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, chain_name="Bittensor"
    ) as substrate:
        block_hash = (
            "0xb0f4a6fb95279f035f145600590e6d5508edea986c2e703e16b6bfbe08f29dbd"
        )
        start = loop.time()
        total_hotkey_alpha_q, total_hotkey_shares_q = await asyncio.gather(
            substrate.query_map(
                "SubtensorModule",
                "TotalHotkeyAlpha",
                block_hash=block_hash,
                page_size=100,
                fully_exhaust=False,
                params=[],
            ),
            substrate.query_map(
                "SubtensorModule",
                "TotalHotkeyShares",
                block_hash=block_hash,
                fully_exhaust=False,
                page_size=100,
                params=[],
            ),
        )
        hotkeys = set()
        tasks: list[asyncio.Task] = []
        sema4 = asyncio.Semaphore(100)
        for (hk, netuid), alpha in total_hotkey_alpha_q.records:
            hotkey = ss58_encode(bytes(hk[0]), 42)
            if alpha.value > 0:
                if hotkey not in hotkeys:
                    hotkeys.add(hotkey)
                    tasks.append(
                        loop.create_task(_query_alpha(hotkey, sema4), name=hotkey)
                    )
        for (hk, netuid), alpha_bits in total_hotkey_shares_q.records:
            hotkey = ss58_encode(bytes(hk[0]), 42)
            alpha_bits_value = alpha_bits.value["bits"]
            if alpha_bits_value > 0:
                if hotkey not in hotkeys:
                    hotkeys.add(hotkey)
                    tasks.append(
                        loop.create_task(_query_alpha(hotkey, sema4), name=hotkey)
                    )
        await asyncio.gather(*tasks)
        end = loop.time()
        return len(tasks), end - start


if __name__ == "__main__":
    results = []
    for _ in range(10):
        len_tasks, time = asyncio.run(benchmark_to_thread_decoding())
        results.append((len_tasks, time))

    for len_tasks, time in results:
        if len_tasks != 910:
            print(len_tasks, time)
    time_results = [x[1] for x in results]
    import statistics

    median = statistics.median(time_results)
    mean = statistics.mean(time_results)
    stdev = statistics.stdev(time_results)
    print(median, mean, stdev)
