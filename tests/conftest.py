import json
from uuid import uuid4

from pytest import fixture
from pytest_lazyfixture import lazy_fixture

from kgforge.core.forges import Forge
from kgforge.core.mapping import Mapper
from kgforge.core.models.resources import Resource
from kgforge.mappers.jsonmapper import JsonMapper


# Utils #


# Paths

@fixture(params=[
    lazy_fixture("filepath"),
    lazy_fixture("dirpath"),
], ids=["file_path", "dir_path"])
def path(request):
    return request.param


@fixture
def filepath(tmp_path):
    path = tmp_path / "file.txt"
    return str(path)


@fixture
def dirpath(tmp_path):
    return str(dirpath)


# Forges #


@fixture
def forge():
    return Forge()


# Mappers #


@fixture
def json_mapper(forge, mapping):
    return JsonMapper(forge, mapping)


@fixture
def json_mapper_flat(forge, flat_mapping):
    return JsonMapper(forge, flat_mapping)


@fixture
def json_mapper_nested(forge, nested_mapping):
    return JsonMapper(forge, nested_mapping)


@fixture
def mapper(forge, mapping):
    return Mapper(forge, mapping)


# Mappings #


@fixture(params=[
    lazy_fixture("flat_mapping"),
    lazy_fixture("nested_mapping"),
], ids=["flat_mapping", "nested_mapping"])
def mapping(request):
    return request.param


@fixture
def flat_mapping():
    return """
        type: Person
        givenName: source.name.split()[0]
        familyName: source.name.split()[1]
    """


@fixture
def nested_mapping(flat_mapping):
    return """
        type: Contribution
        agent: {
            type: Person
            givenName: source.name.split()[0]
            familyName: source.name.split()[1]
        }
    """


# Records #


# JSON

@fixture(params=[
    lazy_fixture("json_record"),
    lazy_fixture("json_record_path"),
], ids=["record", "file"])
def json_data_one(request):
    return request.param


@fixture(params=[
    lazy_fixture("json_flat_record"),
    lazy_fixture("json_nested_record"),
], ids=["flat_record", "nested_record"])
def json_record(request):
    return request.param


@fixture
def json_flat_record(make_json_record):
    return make_json_record("Jane Doe")


@fixture
def json_nested_record(make_json_record):
    return make_json_record("John Smith", nested=True)


@fixture(params=[
    lazy_fixture("json_records"),
    lazy_fixture("json_records_path"),
], ids=["records", "directory"])
def json_data_many(request):
    return request.param


@fixture(params=[
    lazy_fixture("json_records_seq"),
    lazy_fixture("json_records_iter"),
], ids=["records_seq", "records_iter"])
def json_records(request):
    return request.param


@fixture
def json_records_seq(json_flat_record, json_nested_record):
    r1 = json_flat_record
    r2 = json_nested_record
    return [r1, r2]


@fixture
def json_records_iter(json_records_seq):
    return iter(json_records_seq)


@fixture
def json_record_path(tmp_path, json_record):
    path = tmp_path / "json-record.json"
    with path.open("w") as f:
        json.dump(json_record, f)
    return str(path)


@fixture
def json_records_path(tmp_path, json_records_seq):
    for i, x in enumerate(json_records_seq):
        path = tmp_path / f"json-record-{i}.json"
        with path.open("w") as f:
            json.dump(x, f)
    return str(tmp_path)


@fixture
def make_json_record():
    def _make_json_record(name, nested=False):
        base = {
                "type": "Person",
                "name": name,
            }
        if nested:
            addition = {
                "address": {
                    "city": "Geneva",
                    "country": "Switzerland",
                },
            }
        else:
            addition = {}
        return {**base, **addition}
    return _make_json_record


# Resources #


@fixture
def resource(make_resource, resource_properties):
    return make_resource(resource_properties)


@fixture(params=[
    lazy_fixture("resources_seq"),
    lazy_fixture("resources_iter"),
], ids=["resources_seq", "resources_iter"])
def resources(request):
    return request.param


@fixture
def resources_seq(make_resource):
    r1 = make_resource()
    r2 = make_resource()
    return [r1, r2]


@fixture
def resources_iter(resources_seq):
    return iter(resources_seq)


@fixture(params=[
    {},
    {"type": "Person"},
    {"type": "Person", "name": "Jane Doe"},
    lazy_fixture("resource_properties_nested"),
], ids=["no_property", "one_property", "many_properties", "nested_properties"])
def resource_properties(request):
    return request.param


@fixture
def resource_properties_nested(make_resource):
    return {
        "type": "Contribution",
        "agent": make_resource(),
    }


@fixture
def resource_reserved_attributes(forge):
    r = Resource(forge)
    return r.__dict__.keys()


@fixture
def make_resource(forge, make_id):
    def _make_resource(kwargs=None):
        if kwargs is None:
            return Resource(forge, id=make_id())
        else:
            return Resource(forge, id=make_id(), **kwargs)
    return _make_resource


@fixture
def make_id():
    def _make_id():
        return str(uuid4())
    return _make_id
