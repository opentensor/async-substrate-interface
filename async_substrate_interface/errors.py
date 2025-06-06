from websockets.exceptions import ConnectionClosed, InvalidHandshake

ConnectionClosed = ConnectionClosed
InvalidHandshake = InvalidHandshake


class SubstrateRequestException(Exception):
    pass


class MaxRetriesExceeded(SubstrateRequestException):
    pass


class MetadataAtVersionNotFound(SubstrateRequestException):
    def __init__(self):
        message = (
            "Exported method Metadata_metadata_at_version is not found. This indicates the block is quite old, and is"
            "not supported by async-substrate-interface. If you need this, we recommend using the legacy "
            "substrate-interface (https://github.com/JAMdotTech/py-polkadot-sdk)."
        )
        super().__init__(message)


class StateDiscardedError(SubstrateRequestException):
    def __init__(self, block_hash: str):
        self.block_hash = block_hash
        message = (
            f"State discarded for {block_hash}. This indicates the block is too old, and you should instead "
            f"make this request using an archive node."
        )
        super().__init__(message)


class StorageFunctionNotFound(ValueError):
    pass


class BlockNotFound(Exception):
    pass


class ExtrinsicNotFound(Exception):
    pass
