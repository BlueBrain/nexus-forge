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

import pytest
import os
from uuid import uuid4
from urllib.parse import urljoin
from urllib.request import pathname2url

from kgforge.core import KnowledgeGraphForge, Resource
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import _merge_jsonld
from kgforge.core.wrappings.dict import wrap_dict


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


# Fixtures for Resource to JSON-LD conversion and vice versa

@pytest.fixture
def make_registered():
    def _make_registered(r: Resource, metadata, base=None):
        if base:
            r.id = f"{urljoin('file:', pathname2url(os.getcwd()))}/{str(uuid4())}"
        else:
            r.id = str(uuid4())
        if metadata:
            metadata["id"] = r.id
            r._store_metadata = wrap_dict(metadata)
        return r
    return _make_registered


@pytest.fixture
def organization_jsonld_compacted(custom_context, model_context, metadata_data_compacted):
    def _make_jsonld_compacted(r, store_metadata):
        data = dict()
        data["@context"] = model_context.iri if model_context.is_http_iri() else model_context.document["@context"]
        if hasattr(r, "id"):
            data["@id"] = r.id
        nested_context = Context(custom_context)
        data.update({
            "@type": r.type,
            "name": r.name,
            "founder": {
                "@type": r.founder.type,
                "@id": nested_context.resolve(r.founder.id),
                "name": r.founder.name
            }
        })
        if hasattr(r, "id") and store_metadata:
            data.update(metadata_data_compacted)
        return data
    return _make_jsonld_compacted


@pytest.fixture
def person_jsonld_compacted():
    def _make_jsonld_compacted(resource, store_metadata, store_metadata_data, metadata_context):
        data = dict()
        if hasattr(resource, "id"):
            data["@id"] = resource.id
            if store_metadata:
                data["@context"] = _merge_jsonld(resource.context, metadata_context.iri)
            else:
                data["@context"] = resource.context
        data.update({
            "@type": resource.type,
            "@id": resource.id,
            "name": resource.name
        })
        if hasattr(resource, "id") and store_metadata:
            data.update(store_metadata_data)
        return data
    return _make_jsonld_compacted

