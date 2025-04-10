from websockets.exceptions import ConnectionClosed, InvalidHandshake

ConnectionClosed = ConnectionClosed
InvalidHandshake = InvalidHandshake


class SubstrateRequestException(Exception):
    pass


class StorageFunctionNotFound(ValueError):
    pass


class BlockNotFound(Exception):
    pass


class ExtrinsicNotFound(Exception):
    pass
