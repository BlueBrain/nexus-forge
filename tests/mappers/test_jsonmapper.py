from _pytest.mark import param
from pytest import mark
from pytest_lazyfixture import lazy_fixture

from kgforge.core.models.resources import Resource, Resources
from kgforge.mappers.jsonmapper import JsonMapper


class TestJsonMapper:

    def test_apply_scope(self, forge):
        cmd = "json.dumps({'value': 1})"
        mapping = f"property: {cmd}"
        data = {"name": "Jane Doe"}
        mapper = JsonMapper(forge, mapping)
        resource = mapper.apply(data)
        assert resource.property == cmd

    @mark.parametrize("data", [
        param(lazy_fixture("record_path"), id="file"),
        param(lazy_fixture("record"), id="record"),
    ])
    def test_apply_on_data_one(self, json_mapper, data):
        resource = json_mapper.apply(data)
        assert isinstance(resource, Resource)
        assert hasattr(resource, "type")

    @mark.parametrize("data", [
        param(lazy_fixture("records_path"), id="directory"),
        param(lazy_fixture("records"), id="records"),
    ])
    def test_apply_on_data_many(self, json_mapper, data):
        resources = json_mapper.apply(data)
        assert isinstance(resources, Resources)
        resource = resources[-1]
        assert isinstance(resource, Resource)
        assert hasattr(resource, "type")
