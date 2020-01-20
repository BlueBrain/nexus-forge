import pytest

from kgforge.core import KnowledgeGraphForge, Resource


@pytest.fixture
def forge():
    config = {
        "Model": {
            "name": "DemoModel",
            "source": "tests/data/demo-model",
        },
        "Store": {
            "name": "DemoStore",
        },
    }
    return KnowledgeGraphForge(config)


@pytest.fixture
def r1():
    return Resource(id="123", type="Type", p1="v1a", p2="v2a")


@pytest.fixture
def r2():
    return Resource(id="345", type="Type", p1="v1b", p2="v2b")


@pytest.fixture
def r3(r1):
    return Resource(id="678", type="Other", p3="v3c", p4=r1)


@pytest.fixture
def r4(r2):
    return Resource(id="912", type="Other", p3="v3d", p4=r2)


@pytest.fixture
def r5():
    return Resource(p5="v5e", p6="v6e")
