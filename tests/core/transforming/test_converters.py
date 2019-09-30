import pytest

from kgforge.core.transforming.converters import Converters
from tests.data import *


@pytest.mark.parametrize("resource, expected", [
    pytest.param(RESOURCE_1, JSON_LD_1, id="standard-json-ld"),
    pytest.param(RESOURCE_2, JSON_LD_2, id="no-context"),
    pytest.param(RESOURCE_3, JSON_LD_3, id="local-context-list-1"),
    pytest.param(RESOURCE_4, JSON_LD_4, id="local-context-list-2"),
])
def test_as_jsonld(resource, expected):
    data = Converters.as_jsonld(resource, True, False)
    assert data == expected, "data is not as the expected"
