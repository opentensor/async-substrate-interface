import pytest
from websockets.exceptions import InvalidURI

from async_substrate_interface.substrate_interface import AsyncSubstrateInterface


@pytest.mark.asyncio
async def test_invalid_url_raises_exception():
    """Test that invalid URI raises an InvalidURI exception."""
    with pytest.raises(InvalidURI):
        AsyncSubstrateInterface("non_existent_entry_point")
