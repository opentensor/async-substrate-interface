from async_substrate_interface.types import ScaleObj, Runtime, RuntimeCache


def test_scale_object():
    """Verifies that the instance can be subject to various operations."""
    # Preps
    inst_int = ScaleObj(100)

    # Asserts
    assert inst_int + 1 == 101
    assert 1 + inst_int == 101
    assert inst_int - 1 == 99
    assert 101 - inst_int == 1
    assert inst_int * 2 == 200
    assert 2 * inst_int == 200
    assert inst_int / 2 == 50
    assert 100 / inst_int == 1
    assert inst_int // 2 == 50
    assert 1001 // inst_int == 10
    assert inst_int % 3 == 1
    assert 1002 % inst_int == 2
    assert inst_int >= 99
    assert inst_int <= 101

    # Preps
    inst_str = ScaleObj("test")

    # Asserts
    assert inst_str + "test1" == "testtest1"
    assert "test1" + inst_str == "test1test"
    assert inst_str * 2 == "testtest"
    assert 2 * inst_str == "testtest"
    assert inst_str >= "test"
    assert inst_str <= "testtest"
    assert inst_str[0] == "t"
    assert [i for i in inst_str] == ["t", "e", "s", "t"]

    # Preps
    inst_list = ScaleObj([1, 2, 3])

    # Asserts
    assert inst_list[0] == 1
    assert inst_list[-1] == 3
    assert inst_list * 2 == inst_list + inst_list
    assert [i for i in inst_list] == [1, 2, 3]
    assert inst_list >= [1, 2]
    assert inst_list <= [1, 2, 3, 4]
    assert len(inst_list) == 3

    inst_dict = ScaleObj({"a": 1, "b": 2})
    assert inst_dict["a"] == 1
    assert inst_dict["b"] == 2
    assert [i for i in inst_dict] == ["a", "b"]


def test_runtime_cache():
    fake_block = 2
    fake_hash = "0xignore"
    fake_version = 271

    new_fake_block = 3
    newer_fake_block = 4

    new_fake_hash = "0xnewfakehash"

    runtime = Runtime("", None, None)
    runtime_cache = RuntimeCache()
    # insert our Runtime object into the cache with a set block, hash, and version
    runtime_cache.add_item(runtime, fake_block, fake_hash, fake_version)

    assert runtime_cache.retrieve(fake_block) is not None
    # cache does not yet know that new_fake_block has the same runtime
    assert runtime_cache.retrieve(new_fake_block) is None
    assert (
        runtime_cache.retrieve(new_fake_block, runtime_version=fake_version) is not None
    )
    # after checking the runtime with the new block, it now knows this runtime should also map to this block
    assert runtime_cache.retrieve(new_fake_block) is not None
    assert runtime_cache.retrieve(newer_fake_block) is None
    assert runtime_cache.retrieve(newer_fake_block, fake_hash) is not None
    assert runtime_cache.retrieve(newer_fake_block) is not None
    assert runtime_cache.retrieve(block_hash=new_fake_hash) is None
    assert runtime_cache.retrieve(fake_block, block_hash=new_fake_hash) is not None
    assert runtime_cache.retrieve(block_hash=new_fake_hash) is not None
