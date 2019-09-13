class TestDictWrapper:

    def test_init_flat(self, json_flat_record):
        wrapped = DictWrapper.wrap(json_flat_record)
        assert wrapped.name == "Jane Doe"

    def test_init_nested(self, json_nested_record):
        wrapped = DictWrapper.wrap(json_nested_record)
        assert wrapped.name == "John Smith"
        assert wrapped.address.city == "Geneva"
