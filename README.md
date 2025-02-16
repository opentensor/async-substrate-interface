# Async Substrate Interface
This project provides an asynchronous interface for interacting with [Substrate](https://substrate.io/)-based blockchains. It is based on the [py-substrate-interface](https://github.com/polkascan/py-substrate-interface) project.

## Features

- Asynchronous API calls
- Uses [bt-decode](https://github.com/opentensor/bt-decode) instead of [py-scale-codec](https://github.com/polkascan/py-scale-codec) for faster [SCALE](https://polkascan.github.io/py-scale-codec/) decoding.

## Installation

To install the package, use the following command:

```bash
pip install async-substrate-interface
```

## Usage

Here is a basic example of how to use the async-substrate-interface:

```python
import asyncio
from async_substrate_interface import SubstrateInterface

async def main():
    substrate = SubstrateInterface(
        url="wss://rpc.polkadot.io"
    )

    result = await substrate.query(
        module='System',
        storage_function='Account',
        params=['5FHneW46xGXgs5mUiveU4sbTyGBzmto4oT9v5TFn5u4tZ7sY']
    )

    print(result)

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please join the Bittensor Development Discord server: [Church of Rao](https://discord.gg/gavmT4R8sB).
