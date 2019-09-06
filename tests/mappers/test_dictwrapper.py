from kgforge.mappers.jsonmapper import DictWrapper


class TestDictWrapper:

    def test_init_flat(self, flat_record):
        wrapped = DictWrapper.wrap(flat_record)
        assert wrapped.type == "Person"
        assert wrapped.name == "Jane Doe"

    def test_init_nested(self, nested_record):
        wrapped = DictWrapper.wrap(nested_record)
        assert wrapped.type == "Person"
        assert wrapped.name == "John Smith"
        print(wrapped.address)
        assert wrapped.address.city == "Geneva"
