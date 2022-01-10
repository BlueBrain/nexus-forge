#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

import os
from typing import Callable, List, Union, Dict, Optional
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, then, when

from kgforge.core import Resource, KnowledgeGraphForge
from kgforge.core.commons.actions import Action
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import _merge_jsonld, Form
from kgforge.core.wrappings.dict import wrap_dict


def do(fun: Callable, data: Union[Resource, List[Resource]], *args) -> None:
    if isinstance(data, List) and all(isinstance(x, Resource) for x in data):
        for x in data:
            fun(x, *args)
    elif isinstance(data, Resource):
        fun(data, *args)
    else:
        raise TypeError("not a Resource nor a list of Resource")


# It seems using 'given' with both 'fixture' and 'target_fixture' does not work.
# This implies that (in)valid resources creation steps need their dedicated function.


# Resource(s) creation.


@pytest.fixture
def json_one():
    return {"id": "123", "type": "Type", "p1": "v1a", "p2": "v2a"}


@pytest.fixture
def json_list_one():
    return {
        "id": "678",
        "type": "Other",
        "p3": "v3c",
        "p4": [
            {"id": "123", "type": "Type", "p1": "v1a", "p2": "v2a"},
            {"id": "345", "type": "Type", "p1": "v1b", "p2": "v2b"},
        ],
    }


def resource(valid: bool, index: int = 0) -> Resource:
    rid = str(uuid4())
    r = Resource(type="Person", id=rid)
    if valid:
        r.name = f"resource {index}"
    return r


def resources(valid: bool) -> List[Resource]:
    r1 = resource(valid, 0)
    r2 = resource(valid, 1)
    return [r1, r2]


@given("A valid resource.", target_fixture="data")
def valid_resource():
    return resource(True)


@given("Valid resources.", target_fixture="data")
def valid_resources():
    return resources(True)


@given("An invalid resource.", target_fixture="data")
def invalid_resource():
    return resource(False)


@given("Invalid resources.", target_fixture="data")
def invalid_resources():
    return resources(False)


# Resource(s) modifications.


@when("I modify the resource.")
def modify_resource(data):
    data.name = "other"


# Resource(s) verifications.


@then(parsers.parse("The '{attr}' status of {} resource should be '{value}'."))
def check_resource_status(data, attr, value):
    def fun(x):
        assert str(getattr(x, attr)) == value

    do(fun, data)


# Action(s) verifications.


def check_report(capsys, rc, err, msg, op):
    out = capsys.readouterr().out[:-1]
    heads = {
        "": "",
        "s": "<count> 2\n",
    }
    head = heads[rc]
    tails = {
        None: f"False\n<error> {msg}",
        " not": "True",
    }
    tail = tails[err]
    assert out == f"{head}<action> {op}\n<succeeded> {tail}"


@then("I should be able to access the report of the action on a resource.")
def check_action(data):
    def fun(x):
        assert isinstance(x._last_action, Action)

    do(fun, data)


@then(parsers.parse("The report should say that the operation was '{value}'."))
def check_action_operation(data, value):
    def fun(x):
        assert x._last_action.operation == value

    do(fun, data)


@then(parsers.parse("The report should say that the operation success is '{value}'."))
def check_action_success(data, value):
    def fun(x):
        assert str(x._last_action.succeeded) == value

    do(fun, data)


@then(parsers.parse("The report should say that the error was '{value}'."))
def check_action_error(data, value):
    def fun(x):
        assert str(x._last_action.error) == value

    do(fun, data)


# Fixtures for Resource to JSON-LD conversion and vice versa


@pytest.fixture
def forge():
    config = {
        "Model": {
            "name": "DemoModel",
            "origin": "directory",
            "source": "tests/data/demo-model/",
        },
        "Store": {
            "name": "DemoStore",
        },
    }
    return KnowledgeGraphForge(config)


@pytest.fixture
def custom_context():
    return {
        "@context": {
            "@base": "http://example.org/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "Person": "foaf:Person",
            "name": "foaf:name",
        }
    }


@pytest.fixture
def metadata_context() -> Context:
    document = {
        "deprecated": "https://store.net/vocabulary/deprecated",
        "version": "https://store.net/vocabulary/version",
    }
    return Context(document, "http://store.org/metadata.json")


@pytest.fixture
def metadata_data_compacted():
    return {"deprecated": False, "version": 1}


@pytest.fixture
def metadata_data_expanded():
    return {
        "https://store.net/vocabulary/deprecated": False,
        "https://store.net/vocabulary/version": 1,
    }


@pytest.fixture
def store_metadata_context():
    return {
        "meta": "https://store.net/vocabulary/",
        "deprecated": "meta:deprecated",
        "version": "meta:version",
    }


@pytest.fixture
def store_metadata_value(store_metadata_context, metadata_data_compacted):
    data = {"context": store_metadata_context}
    data.update(metadata_data_compacted)
    return data


@pytest.fixture
def person(custom_context):
    return Resource(context=custom_context, type=["Person", "Agent"], name="Jami Booth")


@pytest.fixture
def registered_person_custom_context(person, custom_context, store_metadata_value):
    person.id = "c51f4e4e-2b30-41f4-8f7c-aced85632b03"
    store_metadata_value["id"] = person.id
    person._store_metadata = wrap_dict(store_metadata_value)
    return person


@pytest.fixture
def organization(registered_person_custom_context, store_metadata_value):
    contribution = Resource(
        type=["Organization", "Agent"],
        name="Reichel Inc",
        founder=registered_person_custom_context,
    )
    return contribution


@pytest.fixture
def building():
    type_ = "Building"
    name = "The Empire State Building"
    description = "The Empire State Building is a 102-story landmark in New York City."
    image = "http://www.civil.usherbrooke.ca/cours/gci215a/empire-state-building.jpg"
    geo = {"latitude": "40.75"}
    return Resource(
        type=type_, name=name, description=description, image=image, geo=geo
    )


@pytest.fixture(scope="session")
def context_file_path():
    return os.sep.join((os.path.abspath("."), "tests/data/shacl-model/context.json"))


@pytest.fixture(scope="session")
def context_iri_file(context_file_path):
    return f"file://{context_file_path}"


@pytest.fixture(scope="session")
def context_iri():
    return f"http://example.org/context"


@pytest.fixture(scope="session")
def model_context(context_iri_file) -> Context:
    return Context(context_iri_file, context_iri_file)


@pytest.fixture(scope="session")
def model_prefixes():
    return {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "prov": "http://www.w3.org/ns/prov#",
        "schema": "http://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "nsg": "https://neuroshapes.org/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "foaf": "http://xmlns.com/foaf/0.1/",
    }


@pytest.fixture
def building_jsonld(metadata_context, metadata_data_compacted, metadata_data_expanded):
    def _make_jsonld_expanded(resource, store_metadata, context):
        data = dict()
        if hasattr(resource, "id"):
            data["@id"] = resource.id
        ctx = (
            Context(resource.context)
            if hasattr(resource, "context")
            else Context(context)
        )
        latitude_term = ctx.terms.get("latitude")
        if latitude_term.type:
            latitude_node = {
                "@type": latitude_term.type,
                "@value": resource.geo["latitude"],
            }
        else:
            latitude_node = resource.geo["latitude"]
        geo_expanded = {latitude_term.id: latitude_node}
        data.update(
            {
                "@type": ctx.expand(resource.type),
                ctx.expand("description"): resource.description,
                ctx.expand("geo"): geo_expanded,
                ctx.expand("image"): {"@id": resource.image},
                ctx.expand("name"): resource.name,
            }
        )
        if store_metadata and resource._store_metadata is not None:
            data.update(metadata_data_expanded)
        return data

    def _make_jsonld_compacted(resource, store_metadata, context):
        data = dict()
        data_context = resource.context if hasattr(resource, "context") else context
        if store_metadata and resource._store_metadata is not None:
            metadata_context_output = (
                metadata_context.iri
                if metadata_context.is_http_iri()
                else metadata_context.document["@context"]
            )
            data["@context"] = _merge_jsonld(data_context, metadata_context_output)
        else:
            data["@context"] = data_context
        if hasattr(resource, "id"):
            data["@id"] = resource.id
        data.update(
            {
                "@type": resource.type,
                "description": resource.description,
                "geo": resource.geo,
                "image": resource.image,
                "name": resource.name,
            }
        )
        if store_metadata and resource._store_metadata is not None:
            data.update(metadata_data_compacted)
        return data

    def _make_jsonld(
        rsrc: Resource,
        form: str,
        store_metadata: bool,
        context: Optional[Union[Dict, List, str]],
    ):
        if form is Form.COMPACTED.value:
            return _make_jsonld_compacted(rsrc, store_metadata, context)
        elif form is Form.EXPANDED.value:
            return _make_jsonld_expanded(rsrc, store_metadata, context)

    return _make_jsonld


SCOPE = "terms"
MODEL = "DemoModel"
STORE = "DemoStore"
RESOLVER = "DemoResolver"


@pytest.fixture(
    params=[
        MODEL,
        f"{MODEL} from kgforge.specializations.models",
        f"{MODEL} from kgforge.specializations.models.demo_model",
    ]
)
def model(request):
    return request.param


@pytest.fixture(
    params=[
        STORE,
        f"{STORE} from kgforge.specializations.stores",
        f"{STORE} from kgforge.specializations.stores.demo_store",
    ]
)
def store(request):
    return request.param


@pytest.fixture(
    params=[
        RESOLVER,
        f"{RESOLVER} from kgforge.specializations.resolvers",
        f"{RESOLVER} from kgforge.specializations.resolvers.demo_resolver",
    ]
)
def resolver(request):
    return request.param


@pytest.fixture
def config(model, store, resolver):
    return {
        "Model": {
            "name": model,
            "origin": "directory",
            "source": "tests/data/demo-model/",
        },
        "Store": {
            "name": store,
            "versioned_id_template": "{x.id}?_version={x._store_metadata.version}",
        },
        "Resolvers": {
            SCOPE: [
                {
                    "resolver": resolver,
                    "origin": "directory",
                    "source": "tests/data/demo-resolver/",
                    "targets": [
                        {
                            "identifier": "sex",
                            "bucket": "sex.json",
                        },
                    ],
                    "result_resource_mapping": "../../configurations/demo-resolver/term-to-resource-mapping.hjson",
                },
            ],
        },
    }


@pytest.fixture
def es_mapping_dict():
    return {
        "dynamic": True,
        "properties": {
            "@id": {"type": "keyword"},
            "@type": {"type": "keyword"},
            "annotation": {
                "properties": {
                    "hasBody": {
                        "properties": {
                            "label": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                            "prefLabel": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                        },
                        "type": "nested",
                    }
                },
                "type": "object",
            },
            "atlasRelease": {
                "properties": {
                    "@id": {
                        "fields": {"keyword": {"type": "keyword"}},
                        "type": "keyword",
                    }
                },
                "type": "object",
            },
            "brainLocation": {
                "properties": {
                    "atlasSpatialReferenceSystem": {
                        "properties": {
                            "@id": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "keyword",
                            }
                        },
                        "type": "object",
                    },
                    "brainRegion": {
                        "properties": {
                            "@id": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "keyword",
                            },
                            "label": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                        },
                        "type": "object",
                    },
                    "coordinatesInBrainAtlas": {
                        "properties": {
                            "valueX": {
                                "properties": {
                                    "@type": {"type": "keyword"},
                                    "@value": {
                                        "fields": {"keyword": {"type": "keyword"}},
                                        "type": "float",
                                    },
                                },
                                "type": "object",
                            },
                            "valueY": {
                                "properties": {
                                    "@type": {"type": "keyword"},
                                    "@value": {
                                        "fields": {"keyword": {"type": "keyword"}},
                                        "type": "float",
                                    },
                                },
                                "type": "object",
                            },
                            "valueZ": {
                                "properties": {
                                    "@type": {"type": "keyword"},
                                    "@value": {
                                        "fields": {"keyword": {"type": "keyword"}},
                                        "type": "float",
                                    },
                                },
                                "type": "object",
                            },
                        },
                        "type": "object",
                    },
                    "layer": {
                        "properties": {
                            "label": {
                                "type": "text",
                            }
                        },
                        "type": "object",
                    },
                },
                "type": "object",
            },
            "contribution": {
                "properties": {
                    "agent": {
                        "properties": {
                            "@id": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "keyword",
                            },
                            "@type": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                        },
                        "type": "nested",
                    }
                },
                "type": "nested",
            },
            "derivation": {
                "properties": {
                    "entity": {
                        "properties": {
                            "@type": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                            "name": {
                                "fields": {"keyword": {"type": "keyword"}},
                                "type": "text",
                            },
                        },
                        "type": "nested",
                    },
                    "a_dense_vector": {
                        "dims": 3,
                        "type": "dense_vector",
                    },
                },
                "type": "nested",
            },
            "description": {"fields": {"keyword": {"type": "keyword"}}, "type": "text"},
            "dimension": {"type": "nested"},
            "distribution": {
                "properties": {
                    "contentSize": {"type": "nested"},
                    "contentUrl": {"type": "keyword"},
                    "digest": {
                        "properties": {"value": {"type": "keyword"}},
                        "type": "nested",
                    },
                    "encodingFormat": {"type": "keyword"},
                },
                "type": "nested",
            },
            "generation": {"type": "nested"},
            "isRegisteredIn": {
                "properties": {"@id": {"type": "keyword"}},
                "type": "object",
            },
            "license": {
                "properties": {
                    "label": {
                        "fields": {"keyword": {"type": "keyword"}},
                        "type": "text",
                    }
                },
                "type": "object",
            },
            "name": {"fields": {"keyword": {"type": "keyword"}}, "type": "text"},
            "an_integer": {
                "fields": {"keyword": {"type": "keyword"}},
                "type": "integer",
            },
            "a_dense_vector": {
                "dims": 3,
                "type": "dense_vector",
            },
            "a_boolean": {
                "type": "boolean",
            },
            "objectOfStudy": {
                "properties": {"label": {"type": "text"}},
                "type": "object",
            },
            "parcellationOntology": {
                "properties": {"@id": {"type": "keyword"}},
                "type": "object",
            },
            "parcellationVolume": {
                "properties": {"@id": {"type": "keyword"}},
                "type": "object",
            },
            "recordMeasure": {"type": "nested"},
            "series": {
                "properties": {
                    "statistic": {
                        "fields": {"keyword": {"type": "keyword"}},
                        "type": "text",
                    },
                    "unitCode": {
                        "fields": {"keyword": {"type": "keyword"}},
                        "type": "text",
                    },
                    "a_float": {
                        "type": "float",
                    },
                },
                "type": "nested",
            },
            "spatialReferenceSystem": {
                "properties": {
                    "@id": {
                        "fields": {"keyword": {"type": "keyword"}},
                        "type": "keyword",
                    }
                },
                "type": "object",
            },
            "subject": {"type": "object"},
            "_createdBy": {"type": "keyword"},
            "_updatedBy": {"type": "keyword"},
        },
    }
