from async_substrate_interface.types import ScaleObj


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
