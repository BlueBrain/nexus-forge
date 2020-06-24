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

import json

import pytest
from urllib.error import URLError

from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import _merge_jsonld


def test_load_context_as_dict(custom_context):
    context = Context(custom_context)
    assert is_valid_document(context.document)
    assert context.document == custom_context
    assert context.iri is None
    assert context.is_http_iri() is False


def test_load_context_from_file(context_file_path, context_iri_file):
    with open(context_file_path) as f:
        context_json = json.loads(f.read())
    context = Context(context_iri_file, context_iri_file)
    assert is_valid_document(context.document)
    assert context.document == context_json
    assert context.iri is context_iri_file
    assert context.is_http_iri() is False


def test_load_context_from_list(custom_context, context_iri_file, model_prefixes):
    test_context = _merge_jsonld(custom_context, context_iri_file)
    context = Context(test_context)
    assert is_valid_document(context.document)
    assert context.iri is None
    assert context.is_http_iri() is False
    assert context.base == "http://example.org/"
    assert context.vocab == "http://example.org/vocab/"
    assert context.expand("Person") == "http://schema.org/Person"
    assert context.prefixes == model_prefixes


def test_load_context_from_url():
    context_url = "https://json-ld.org/contexts/person.jsonld"
    context = Context(context_url, context_url)
    assert is_valid_document(context.document)
    assert context.expand("affiliation") == "http://schema.org/affiliation"
    assert context.iri == context_url
    assert context.is_http_iri() is True


def test_load_context_fail():
    context_url = "https://unresolvable.context.org"
    with pytest.raises(URLError):
        Context(context_url)


def is_valid_document(doc):
    return (isinstance(doc, dict)
            and "@context" in doc)
