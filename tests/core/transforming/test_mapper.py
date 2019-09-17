import hjson
from pytest import raises

from kgforge.core.resources import Resources
from kgforge.core.transforming.mapping import Mapper


class TestMapper:

    def test_init(self, forge, mapping):
        loaded = hjson.loads(mapping)
        mapper = Mapper(forge, mapping)
        assert mapper.mapping == loaded

    def test_apply_one(self, mapper, json_record):
        with raises(NotImplementedError):
            mapper._map_one(json_record)

    def test_apply_many(self, mocker, mapper, json_records):
        mocker.patch("kgforge.core.mapping.Mapper.map_one")
        resources = mapper._map_many(json_records)
        assert Mapper._map_one.call_count == 2
        assert isinstance(resources, Resources)

    def test_apply_on_path(self, mapper, path):
        with raises(NotImplementedError):
            mapper.map(path)

    def test_apply_on_one(self, mocker, mapper, json_record):
        mocker.patch("kgforge.core.mapping.Mapper.map_one")
        mapper.map(json_record)
        Mapper._map_one.assert_called_once()

    def test_apply_on_many(self, mocker, mapper, json_records):
        mocker.patch("kgforge.core.mapping.Mapper.map_many")
        mapper.map(json_records)
        Mapper._map_many.assert_called_once()
