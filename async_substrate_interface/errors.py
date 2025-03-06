from typing import Dict


class _SubstrateRequestExceptionMeta(type):
    _exceptions: Dict[str, Exception] = {}

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)

        mcs._exceptions.setdefault(cls.__name__, cls)

        return cls


class SubstrateRequestException(Exception, metaclass=_SubstrateRequestExceptionMeta):
    @classmethod
    def from_error(cls, error):
        try:
            Exception = _SubstrateRequestExceptionMeta._exceptions[error["name"]]
        except KeyError:
            return cls(error)
        else:
            return Exception(" ".join(error["docs"]))


class HotKeyAccountNotExists(SubstrateRequestException):
    """
    The hotkey does not exists
    """


class NonAssociatedColdKey(SubstrateRequestException):
    """
    Request to stake, unstake or subscribe is made by a coldkey that is not associated with the hotkey account.
    """


class DelegateTakeTooHigh(SubstrateRequestException):
    """
    Delegate take is too high.
    """


class DelegateTakeTooLow(SubstrateRequestException):
    """
    Delegate take is too low.
    """


class DelegateTxRateLimitExceeded(SubstrateRequestException):
    """
    A transactor exceeded the rate limit for delegate transaction.
    """


class StorageFunctionNotFound(ValueError):
    pass


class BlockNotFound(Exception):
    pass


class ExtrinsicNotFound(Exception):
    pass
