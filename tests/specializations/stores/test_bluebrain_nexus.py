import pytest

from kgforge.specializations.stores.bluebrain_nexus import BlueBrainNexus
from tests.data import *

BUCKET = "test/kgforge"
NEXUS = "https://nexus-instance.org/"
TOKEN = "token"


@pytest.fixture
def nexus_store():
    # FIXME mock Nexus for unittests
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token=TOKEN)


@pytest.fixture
def nexus_store_unauthorized():
    return BlueBrainNexus(endpoint=NEXUS, bucket=BUCKET, token="invalid token")


def test_config_error():
    with pytest.raises(ValueError):
        BlueBrainNexus(endpoint="test", bucket="invalid", token="")


def test_config(nexus_store):
    assert nexus_store.organisation == "test"
    assert nexus_store.project == "kgforge"
    assert nexus_store.endpoint == NEXUS


@pytest.mark.parametrize("data, expected", [
    pytest.param(JSON_LD_1, RESOURCE_1, id="standard-json-ld"),
    pytest.param(JSON_LD_2, RESOURCE_2, id="no-context-"),
    pytest.param(JSON_LD_3, RESOURCE_3, id="local-context-list-1"),
    pytest.param(JSON_LD_5, RESOURCE_5, id="context-and-meta")
])
def test_response_to_resource(nexus_store, data, expected):
    resource = nexus_store._to_resource(data)
    assert_equal(expected, resource), "resource is not as the expected"


def assert_equal(first, second):
    assert str(first) == str(second)
    assert getattr(first, "_context", None) == getattr(first, "_context", None)
