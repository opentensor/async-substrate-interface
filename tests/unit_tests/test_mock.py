from websockets.exceptions import InvalidURI
import pytest

from async_substrate_interface import AsyncSubstrateInterface, SubstrateInterface


@pytest.mark.asyncio
async def test_async_mock():
    ssi = AsyncSubstrateInterface("notreal")
    assert isinstance(ssi, AsyncSubstrateInterface)
    with pytest.raises(InvalidURI):
        await ssi.initialize()
    async with AsyncSubstrateInterface("notreal", _mock=True) as ssi:
        assert isinstance(ssi, AsyncSubstrateInterface)
    ssi = AsyncSubstrateInterface("notreal", _mock=True)
    async with ssi:
        pass


def test_sync_mock():
    with pytest.raises(InvalidURI):
        SubstrateInterface("notreal")
    ssi = SubstrateInterface("notreal", _mock=True)
    assert isinstance(ssi, SubstrateInterface)
    with pytest.raises(InvalidURI):
        with SubstrateInterface("notreal") as ssi:
            pass
    with SubstrateInterface("notreal", _mock=True) as ssi:
        assert isinstance(ssi, SubstrateInterface)
