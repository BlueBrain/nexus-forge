import hjson
from pytest import raises

from kgforge.core.transforming.mapping import Mapper
from kgforge.core.resources import Resources


class TestMapper:

    def test_init(self, forge, mapping):
        loaded = hjson.loads(mapping)
        mapper = Mapper(forge, mapping)
        assert mapper.mapping == loaded

    def test_apply_one(self, mapper, json_record):
        with raises(NotImplementedError):
            mapper.apply_one(json_record)

    def test_apply_many(self, mocker, mapper, json_records):
        mocker.patch("kgforge.core.mapping.Mapper.apply_one")
        resources = mapper.apply_many(json_records)
        assert Mapper.apply_one.call_count == 2
        assert isinstance(resources, Resources)

    def test_apply_on_path(self, mapper, path):
        with raises(NotImplementedError):
            mapper.apply(path)

    def test_apply_on_one(self, mocker, mapper, json_record):
        mocker.patch("kgforge.core.mapping.Mapper.apply_one")
        mapper.apply(json_record)
        Mapper.apply_one.assert_called_once()

    def test_apply_on_many(self, mocker, mapper, json_records):
        mocker.patch("kgforge.core.mapping.Mapper.apply_many")
        mapper.apply(json_records)
        Mapper.apply_many.assert_called_once()
