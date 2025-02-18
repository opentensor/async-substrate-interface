# Async Substrate Interface
This project provides an asynchronous interface for interacting with [Substrate](https://substrate.io/)-based blockchains. It is based on the [py-substrate-interface](https://github.com/polkascan/py-substrate-interface) project.

Additionally, this project uses [bt-decode](https://github.com/opentensor/bt-decode) instead of [py-scale-codec](https://github.com/polkascan/py-scale-codec) for faster [SCALE](https://docs.substrate.io/reference/scale-codec/) decoding.

## Installation

To install the package, use the following command:

```bash
pip install async-substrate-interface
```

## Usage

Here are examples of how to use the sync and async inferfaces:

```python
from async_substrate_interface import SubstrateInterface

def main():
    substrate = SubstrateInterface(
        url="wss://rpc.polkadot.io"
    )
    with substrate:
        result = substrate.query(
            module='System',
            storage_function='Account',
            params=['5CZs3T15Ky4jch1sUpSFwkUbYEnsCfe1WCY51fH3SPV6NFnf']
        )

        print(result)

main()
```

```python
import asyncio
from async_substrate_interface import AsyncSubstrateInterface

async def main():
    substrate = AsyncSubstrateInterface(
        url="wss://rpc.polkadot.io"
    )
    async with substrate:
        result = await substrate.query(
            module='System',
            storage_function='Account',
            params=['5CZs3T15Ky4jch1sUpSFwkUbYEnsCfe1WCY51fH3SPV6NFnf']
        )

        print(result)

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request to the `staging` branch.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please join the Bittensor Development Discord server: [Church of Rao](https://discord.gg/XC7ucQmq2Q).
