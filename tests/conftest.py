import subprocess
import time

CONTAINER_NAME_PREFIX = "test_local_chain_"
LOCALNET_IMAGE_NAME = "ghcr.io/opentensor/subtensor-localnet:devnet-ready"


def start_docker_container(exposed_port, name_salt: str):
    container_name = f"{CONTAINER_NAME_PREFIX}{name_salt}"

    # Command to start container
    cmds = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "-p",
        f"{exposed_port}:9945",
        LOCALNET_IMAGE_NAME,
    ]

    proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc, container_name
