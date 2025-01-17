import pytest
from websockets.exceptions import InvalidURI

from async_substrate_interface.async_substrate import (
    AsyncSubstrateInterface
)


@pytest.mark.asyncio
async def test_invalid_url_raises_exception():
    """Test that invalid URI raises an InvalidURI exception."""
    async_substrate = AsyncSubstrateInterface("non_existent_entry_point")
    with pytest.raises(InvalidURI):
        await async_substrate.initialize()

    with pytest.raises(InvalidURI):
        async with AsyncSubstrateInterface(
            "non_existent_entry_point"
        ) as async_substrate:
            pass
