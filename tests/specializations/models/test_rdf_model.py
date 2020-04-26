#
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.
import json
import pytest

from kgforge.specializations.models import RdfModel
from tests.specializations.models.data import *


@pytest.fixture
def rdf_model(context_iri_file):
    return RdfModel("tests/data/shacl-model",
                    context={"iri": context_iri_file},
                    origin="directory")


class TestVocabulary:

    def test_generate_context(self, rdf_model: RdfModel):
        generated_context = rdf_model._generate_context()
        for k in TYPES_SCHEMAS_MAP.keys():
            assert generated_context.expand(k) is not None

    def test_types(self, rdf_model: RdfModel):
        types = rdf_model.types(pretty=False)
        assert types == list(TYPES_SCHEMAS_MAP.keys())

    def test_context(self, rdf_model: RdfModel, context_file_path):
        with open(context_file_path) as f:
            expected = json.load(f)
        vocabulary = rdf_model.context().document
        assert vocabulary == expected

    def test_namespaces(self, rdf_model: RdfModel, model_prefixes):
        assert rdf_model.prefixes(pretty=False) == model_prefixes


class TestTemplates:

    def test_request_invalid_type(self, rdf_model: RdfModel):
        with pytest.raises(ValueError):
            rdf_model._template("Invalid", False)

    @pytest.mark.parametrize("type_, expected", [
        pytest.param("Person", PERSON, id="person"),
        pytest.param("Employee", EMPLOYEE, id="employee"),
        pytest.param("Activity", ACTIVITY, id="activity"),
        pytest.param("Building", BUILDING, id="building"),
    ])
    def test_create_templates(self, rdf_model: RdfModel, type_, expected):
        result = rdf_model._template(type_, False)
        assert result == expected

    @pytest.mark.parametrize("type_, expected", [
        pytest.param("Activity", ACTIVITY_MANDATORY, id="activity"),
        pytest.param("Building", BUILDING_MANDATORY, id="building"),
    ])
    def test_create_templates_only_required(self, rdf_model: RdfModel, type_, expected):
        result = rdf_model._template(type_, True)
        assert result == expected


class TestValidation:

    @pytest.mark.parametrize("type_,", TYPES_SCHEMAS_MAP.keys())
    def test_schema_id(self, rdf_model: RdfModel, type_):
        assert rdf_model.schema_id(type_) == TYPES_SCHEMAS_MAP[type_]
