class SubstrateRequestException(Exception):
    pass


class StorageFunctionNotFound(ValueError):
    pass


class BlockNotFound(Exception):
    pass


class ExtrinsicNotFound(Exception):
    pass
