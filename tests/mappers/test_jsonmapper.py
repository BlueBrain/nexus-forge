from _pytest.mark import param
from pytest import mark
from pytest_lazyfixture import lazy_fixture

from kgforge.core.models.resources import Resource, Resources
from kgforge.mappers.jsonmapper import DictWrapper, JsonMapper


class TestDictWrapper:

    def test_init_flat(self, json_flat_record):
        wrapped = DictWrapper.wrap(json_flat_record)
        assert wrapped.name == "Jane Doe"

    def test_init_nested(self, json_nested_record):
        wrapped = DictWrapper.wrap(json_nested_record)
        assert wrapped.name == "John Smith"
        assert wrapped.address.city == "Geneva"


class TestJsonMapper:

    def test_apply_scope(self, forge):
        rule = "json.dumps({'value': 1})"
        mapping = f"property: {rule}"
        data = {"name": "Jane Doe"}
        mapper = JsonMapper(forge, mapping)
        resource = mapper.apply(data)
        assert resource.property == rule

    @mark.parametrize("data", [
        param(lazy_fixture("json_record_path"), id="file"),
        param(lazy_fixture("json_record"), id="record"),
    ])
    def test_apply_on_data_one(self, json_mapper, data):
        resource = json_mapper.apply(data)
        assert isinstance(resource, Resource)
        assert hasattr(resource, "type")
        # FIXME Nested Resource creation testing.

    @mark.parametrize("data", [
        param(lazy_fixture("json_records_path"), id="directory"),
        param(lazy_fixture("json_records"), id="records"),
    ])
    def test_apply_on_data_many(self, json_mapper, data):
        resources = json_mapper.apply(data)
        assert isinstance(resources, Resources)
        resource = resources[-1]
        assert isinstance(resource, Resource)
        assert hasattr(resource, "type")
