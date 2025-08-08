from tests.helpers.fixtures import import_fresh


def test_env_vars(monkeypatch):
    monkeypatch.setenv("SUBSTRATE_CACHE_METHOD_SIZE", 10)
    monkeypatch.setenv("SUBSTRATE_RUNTIME_CACHE_SIZE", 9)
    sync_substrate = import_fresh("async_substrate_interface.sync_substrate")
    asi = sync_substrate.SubstrateInterface("", _mock=True)
    assert asi.get_runtime_for_version.cache_parameters()["maxsize"] == 9
    assert asi.get_block_runtime_info.cache_parameters()["maxsize"] == 9
    assert asi.get_parent_block_hash.cache_parameters()["maxsize"] == 10
    assert asi.get_block_runtime_version_for.cache_parameters()["maxsize"] == 10
    assert asi.get_block_hash.cache_parameters()["maxsize"] == 10


def test_defaults():
    sync_substrate = import_fresh("async_substrate_interface.sync_substrate")
    asi = sync_substrate.SubstrateInterface("", _mock=True)
    assert asi.get_runtime_for_version.cache_parameters()["maxsize"] == 16
    assert asi.get_block_runtime_info.cache_parameters()["maxsize"] == 16
    assert asi.get_parent_block_hash.cache_parameters()["maxsize"] == 512
    assert asi.get_block_runtime_version_for.cache_parameters()["maxsize"] == 512
    assert asi.get_block_hash.cache_parameters()["maxsize"] == 512
