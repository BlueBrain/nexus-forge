import hjson
from pytest import raises

from kgforge.core.mapping import Mapper
from kgforge.core.models.resources import Resources


class TestMapper:

    def test_init(self, forge, mapping):
        loaded = hjson.loads(mapping)
        mapper = Mapper(forge, mapping)
        assert mapper.mapping == loaded

    def test_apply_one(self, mapper, record):
        with raises(NotImplementedError):
            mapper.apply_one(record)

    def test_apply_many(self, mocker, mapper, records):
        mocker.patch("kgforge.core.mapping.Mapper.apply_one")
        resources = mapper.apply_many(records)
        assert Mapper.apply_one.call_count == 2
        assert isinstance(resources, Resources)

    def test_apply_on_path(self, record_path, mapper):
        with raises(NotImplementedError):
            mapper.apply(record_path)

    def test_apply_on_one(self, mocker, mapper, record):
        mocker.patch("kgforge.core.mapping.Mapper.apply_one")
        mapper.apply(record)
        Mapper.apply_one.assert_called_once()

    def test_apply_on_many(self, mocker, mapper, records):
        mocker.patch("kgforge.core.mapping.Mapper.apply_many")
        mapper.apply(records)
        Mapper.apply_many.assert_called_once()
