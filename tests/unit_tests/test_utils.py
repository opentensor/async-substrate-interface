from async_substrate_interface.utils import get_next_id
from string import ascii_letters


def test_get_next_id():
    next_id = get_next_id()
    assert next_id[0] in ascii_letters
    assert next_id[1] in ascii_letters
    assert 0 < int(next_id[2:]) < 999
    assert 3 <= len(next_id) <= 5
