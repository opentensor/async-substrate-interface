import threading
import subprocess

import pytest
import time

from async_substrate_interface.substrate_addons import RetrySyncSubstrate
from async_substrate_interface.errors import MaxRetriesExceeded
from tests.conftest import start_docker_container

LATENT_LITE_ENTRYPOINT = "wss://lite.sub.latent.to:443"


@pytest.fixture(scope="function")
def docker_containers():
    processes = (start_docker_container(9945, 9945), start_docker_container(9946, 9946))
    try:
        yield processes

    finally:
        for process in processes:
            subprocess.run(["docker", "kill", process.name])
            process.process.kill()


@pytest.fixture(scope="function")
def single_local_chain():
    process = start_docker_container(9945, 9945)
    try:
        yield process
    finally:
        print("TRIGGERED KILL")
        subprocess.run(["docker", "kill", process.name])
        process.process.kill()


def test_retry_sync_substrate(single_local_chain):
    time.sleep(10)
    with RetrySyncSubstrate(
        single_local_chain.uri, fallback_chains=[LATENT_LITE_ENTRYPOINT]
    ) as substrate:
        for i in range(10):
            assert substrate.get_chain_head().startswith("0x")
            if i == 8:
                subprocess.run(["docker", "stop", single_local_chain.name])
            if i > 8:
                assert substrate.chain_endpoint == LATENT_LITE_ENTRYPOINT
            time.sleep(2)


def test_retry_sync_substrate_max_retries(docker_containers):
    time.sleep(10)
    with RetrySyncSubstrate(
        docker_containers[0].uri, fallback_chains=[docker_containers[1].uri]
    ) as substrate:
        for i in range(5):
            print("EYE EQUALS", i)
            assert substrate.get_chain_head().startswith("0x")
            if i == 2:
                subprocess.run(["docker", "pause", docker_containers[0].name])
            if i == 3:
                assert substrate.chain_endpoint == docker_containers[1].uri
            if i == 4:
                subprocess.run(["docker", "pause", docker_containers[1].name])
                with pytest.raises(MaxRetriesExceeded):
                    substrate.get_chain_head().startswith("0x")
            time.sleep(2)


def test_retry_sync_substrate_offline():
    with pytest.raises(ConnectionError):
        RetrySyncSubstrate(
            "ws://127.0.0.1:9945", fallback_chains=["ws://127.0.0.1:9946"]
        )
