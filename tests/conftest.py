import json
from uuid import uuid4

from pytest import fixture
from pytest_lazyfixture import lazy_fixture

from kgforge.core.forges import Forge
from kgforge.core.mapping import Mapper
from kgforge.core.models.resources import Resource
from kgforge.mappers.jsonmapper import JsonMapper


# Forges


@fixture
def forge():
    return Forge()


# Mappings


@fixture
def json_mapper(forge, mapping):
    return JsonMapper(forge, mapping)


@fixture
def mapper(forge, mapping):
    return Mapper(forge, mapping)


@fixture(params=[
    lazy_fixture("flat_mapping"),
    lazy_fixture("nested_mapping"),
], ids=["flat", "nested"])
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


@fixture
def flat_record(make_record):
    return make_record("Jane Doe", False)


@fixture
def nested_record(make_record):
    return make_record("John Smith", True)


@fixture(params=[
    lazy_fixture("flat_record"),
    lazy_fixture("nested_record"),
], ids=["flat", "nested"])
def record(request):
    return request.param


@fixture(params=[
    lazy_fixture("records_seq"),
    lazy_fixture("records_iter"),
], ids=["sequence", "iterator"])
def records(request):
    return request.param


@fixture
def records_seq(make_record):
    r1 = make_record("Jane Doe", False)
    r2 = make_record("John Smith", True)
    return [r1, r2]


@fixture
def records_iter(records_seq):
    return iter(records_seq)


@fixture
def record_path(tmp_path, record):
    path = tmp_path / "record.json"
    with path.open("w") as f:
        json.dump(record, f)
    return str(path)


@fixture
def records_path(tmp_path, records_seq):
    for i, x in enumerate(records_seq):
        path = tmp_path / f"record-{i}.json"
        with path.open("w") as f:
            json.dump(x, f)
    return str(tmp_path)


@fixture
def make_record():
    def _make_record(name, nested=False):
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
    return _make_record


# Resources


@fixture(params=[
    {},
    {"type": "Person"},
    {"type": "Person", "name": "Jane Doe"},
    lazy_fixture("properties_with_resource"),
], ids=["none", "one", "many", "with_resource"])
def properties(request):
    return request.param


@fixture
def properties_with_resource(make_resource):
    return {
        "type": "Contribution",
        "agent": make_resource(),
    }


@fixture
def resource(make_resource, properties):
    return make_resource(properties)


@fixture(params=[
    lazy_fixture("resources_seq"),
    lazy_fixture("resources_iter"),
], ids=["sequence", "iterator"])
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
