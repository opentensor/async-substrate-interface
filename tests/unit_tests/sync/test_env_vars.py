import importlib
import sys


def import_fresh(modname: str):
    """
    Imports or reloads the module from a fresh state.
    """
    to_drop = [m for m in sys.modules if m == modname or m.startswith(modname + ".")]
    for m in to_drop:
        sys.modules.pop(m)
    return importlib.import_module(modname)


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
