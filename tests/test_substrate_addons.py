import threading
import subprocess

import pytest
import time

from async_substrate_interface.substrate_addons import RetrySyncSubstrate
from tests.conftest import start_docker_container


@pytest.fixture(scope="function")
def start_containers():
    # Store our subprocesses globally
    processes = (start_docker_container(9945, 9945), start_docker_container(9946, 9946))
    yield processes

    # To stop the instances, you can iterate over the processes and kill them:
    for process in processes:
        subprocess.run(["docker", "kill", process[1]])
        process[0].kill()


def test_retry_sync_substrate(start_containers):
    container1, container2 = start_containers
    time.sleep(10)
    with RetrySyncSubstrate(
        "ws://127.0.0.1:9945", fallback_chains=["ws://127.0.0.1:9946"]
    ) as substrate:
        for i in range(10):
            assert substrate.get_chain_head().startswith("0x")
            if i == 8:
                subprocess.run(["docker", "kill", container1[1]])
                time.sleep(10)
            if i > 8:
                assert substrate.chain_endpoint == "ws://127.0.0.1:9946"
            time.sleep(2)
