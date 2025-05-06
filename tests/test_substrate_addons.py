import threading
import subprocess

import pytest
import time

from async_substrate_interface.substrate_addons import RetrySyncSubstrate
from tests.conftest import start_docker_container


@pytest.fixture(scope="function")
def docker_containers():
    processes = (start_docker_container(9945, 9945), start_docker_container(9946, 9946))
    try:
        yield processes

    finally:
        for process in processes:
            subprocess.run(["docker", "kill", process[1]])
            process[0].kill()


def test_retry_sync_substrate(docker_containers):
    time.sleep(10)
    with RetrySyncSubstrate(
        docker_containers[0].uri, fallback_chains=[docker_containers[1].uri]
    ) as substrate:
        for i in range(10):
            assert substrate.get_chain_head().startswith("0x")
            if i == 8:
                subprocess.run(["docker", "stop", docker_containers[0].name])
                time.sleep(10)
            if i > 8:
                assert substrate.chain_endpoint == docker_containers[1].uri
            time.sleep(2)


def test_retry_sync_substrate_offline():
    with pytest.raises(ConnectionError):
        RetrySyncSubstrate(
            "ws://127.0.0.1:9945", fallback_chains=["ws://127.0.0.1:9946"]
        )
