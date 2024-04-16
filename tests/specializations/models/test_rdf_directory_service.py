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
from pathlib import Path
import pytest
from rdflib import Dataset as RDFDataset
from rdflib import Graph
from rdflib.term import URIRef
from kgforge.specializations.models import RdfModel
from kgforge.specializations.models.rdf.directory_service import (
    _load_rdf_files_as_graph,
)
from tests.specializations.models.data import TYPES_SHAPES_MAP


def test_load_rdf_files_as_graph(shacl_schemas_file_path):
    graph_dataset = _load_rdf_files_as_graph(Path(shacl_schemas_file_path))
    assert isinstance(graph_dataset, RDFDataset)
    shape_graphs = [str(g.identifier) for g in graph_dataset.graphs()]
    assert len(shape_graphs) == 6
    expected_file_paths = [
        str(f.resolve())
        for f in Path(shacl_schemas_file_path).rglob(os.path.join("*.*"))
    ]
    expected_named_graphs = expected_file_paths + ["urn:x-rdflib:default"]
    assert sorted(shape_graphs) == sorted(expected_named_graphs)
    for file_path in expected_file_paths:
        g = graph_dataset.graph(file_path)
        expected_g = Graph().parse(file_path, format="json-ld")
        assert len(g) > 0
        assert len(g) == len(expected_g)


def test_load_not_existing_rdf_files_raise_error():
    with pytest.raises(ValueError):
        _load_rdf_files_as_graph(Path("not_existing_shacl_schemas_file_path"))


def test_build_shapes_map(rdf_model_from_dir: RdfModel):
    (class_to_shape, shape_to_defining_resource, defining_resource_to_named_graph) = (
        rdf_model_from_dir.service._build_shapes_map()
    )

    geo_shape_uri = (
        "http://www.example.com/GeoShape"  # The only shape not targeting a class
    )
    assert sorted(list(class_to_shape.values()) + [URIRef(geo_shape_uri)]) == sorted(
        list(shape_to_defining_resource.keys())
    )
    assert sorted(set(shape_to_defining_resource.values())) == sorted(
        set(defining_resource_to_named_graph.keys())
    )
    expected_targeted_classes = list(TYPES_SHAPES_MAP.keys())
    loaded_classes = [
        rdf_model_from_dir.service.context.to_symbol(cls)
        for cls in class_to_shape.keys()
    ]
    assert sorted(loaded_classes) == sorted(expected_targeted_classes)
    expected_shapes = [val["shape"] for val in TYPES_SHAPES_MAP.values()]
    expected_shapes.append(geo_shape_uri)
    loaded_shapes = [str(s) for s in shape_to_defining_resource.keys()]
    assert sorted(loaded_shapes) == sorted(expected_shapes)


def test_build_ontology_map(rdf_model_from_dir: RdfModel):
    ont_to_named_graph = rdf_model_from_dir.service._build_ontology_map()
    assert isinstance(ont_to_named_graph, dict)
    f = Path("tests/data/shacl-model/commons/schemaorg-v26.0.json")
    assert ont_to_named_graph == {
        URIRef("https://schema.org/"): URIRef(str(f.resolve()))
    }
