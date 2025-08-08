from tests.helpers.fixtures import import_fresh


def test_env_vars(monkeypatch):
    monkeypatch.setenv("SUBSTRATE_CACHE_METHOD_SIZE", 10)
    monkeypatch.setenv("SUBSTRATE_RUNTIME_CACHE_SIZE", 9)
    async_substrate = import_fresh("async_substrate_interface.async_substrate")
    asi = async_substrate.AsyncSubstrateInterface("", _mock=True)
    assert asi.get_runtime_for_version._max_size == 9
    assert asi.get_block_runtime_info._max_size == 9
    assert asi.get_parent_block_hash._max_size == 10
    assert asi.get_block_runtime_version_for._max_size == 10
    assert asi.get_block_hash._max_size == 10


def test_defaults():
    async_substrate = import_fresh("async_substrate_interface.async_substrate")
    asi = async_substrate.AsyncSubstrateInterface("", _mock=True)
    assert asi.get_runtime_for_version._max_size == 16
    assert asi.get_block_runtime_info._max_size == 16
    assert asi.get_parent_block_hash._max_size == 512
    assert asi.get_block_runtime_version_for._max_size == 512
    assert asi.get_block_hash._max_size == 512
