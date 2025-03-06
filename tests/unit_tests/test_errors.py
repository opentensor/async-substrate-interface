from async_substrate_interface.errors import (
    SubstrateRequestException,
    HotKeyAccountNotExists,
)


def test_from_error():
    error = {
        "type": "Module",
        "name": "HotKeyAccountNotExists",
        "docs": ["The hotkey does not exists"],
    }

    exception = SubstrateRequestException.from_error(error)

    assert isinstance(exception, HotKeyAccountNotExists)
    assert exception.args[0] == "The hotkey does not exists"


def test_from_error_unsupported_exception():
    error = {
        "type": "Module",
        "name": "UnknownException",
        "docs": ["Unknown"],
    }

    exception = SubstrateRequestException.from_error(error)

    assert isinstance(exception, SubstrateRequestException)
    assert exception.args[0] == error


def test_from_error_new_exception():
    error = {
        "type": "Module",
        "name": "NewException",
        "docs": ["New"],
    }

    exception = SubstrateRequestException.from_error(error)

    assert isinstance(exception, SubstrateRequestException)

    class NewException(SubstrateRequestException):
        pass

    exception = SubstrateRequestException.from_error(error)

    assert isinstance(exception, NewException)
