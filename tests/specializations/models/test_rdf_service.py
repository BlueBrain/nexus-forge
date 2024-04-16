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


from pyshacl import Shape
import pytest
from rdflib import OWL, RDF, SH, Graph, URIRef
from kgforge.specializations.models.rdf.directory_service import DirectoryService
from kgforge.specializations.models.rdf_model import RdfModel
from tests.specializations.models.data import TYPES_SHAPES_MAP


def test_get_shape_graph(rdf_model_from_dir: RdfModel):
    assert isinstance(rdf_model_from_dir.service, DirectoryService)
    for s in TYPES_SHAPES_MAP.values():
        shape, schema_graph, ont_graph = rdf_model_from_dir.service.get_shape_graph(
            URIRef(s["shape"])
        )
        assert isinstance(shape, Shape)
        assert str(shape.node) == s["shape"]
        assert isinstance(schema_graph, Graph)
        assert isinstance(ont_graph, Graph)
        assert shape.node == URIRef(s["shape"])
        assert (shape.node, None, None) in schema_graph
        assert len(schema_graph) > 0

        for imported in s["imports"]["schema"]:
            imported_named_graph_uriref = (
                rdf_model_from_dir.service.defining_resource_to_named_graph[
                    URIRef(imported)
                ]
            )
            imported_named_graph = (
                rdf_model_from_dir.service.load_resource_graph_from_source(
                    graph_id=imported_named_graph_uriref, schema_id=imported
                )
            )
            for t in imported_named_graph:
                assert t in schema_graph

            _, imported_sh_properties = (
                rdf_model_from_dir.service.get_nodeshape_parent_propertyshape(
                    imported_named_graph, URIRef(imported)
                )
            )
            for sh_property in imported_sh_properties:
                assert (URIRef(s["shape"]), SH.property, sh_property) in schema_graph
        if s["imports"]["ontology"]:
            assert len(ont_graph) == 34872
        for imported_ont in s["imports"]["ontology"]:
            assert (URIRef(imported_ont), None, None) not in schema_graph
            assert (URIRef(imported_ont), RDF.type, OWL.Ontology) in ont_graph


def test_get_nodeshape_parent_propertyshape(rdf_model_from_dir):
    assert len(rdf_model_from_dir.service._imported) == 0
    for s in TYPES_SHAPES_MAP.values():
        schema_graph, _ = rdf_model_from_dir.service._transitive_load_resource_graph(
            rdf_model_from_dir.service._get_named_graph_from_shape(URIRef(s["shape"])),
            rdf_model_from_dir.service.shape_to_defining_resource[URIRef(s["shape"])],
        )
        sh_nodes, sh_properties = (
            rdf_model_from_dir.service.get_nodeshape_parent_propertyshape(
                schema_graph, URIRef(s["shape"])
            )
        )
        assert len(set(sh_properties)) == s["number_of_direct_property_shapes"]
        assert sorted(list(sh_nodes)) == sorted(s["parent_node_shapes"])
        (
            triples_to_add,
            node_transitive_property_shapes,
            triples_to_remove,
            rdfcollection_items_to_remove,
        ) = rdf_model_from_dir.service._get_transitive_property_shapes_from_nodeshape(
            URIRef(s["shape"]), schema_graph
        )
        assert len(triples_to_add) == s["number_of_inherited_property_shapes"]
        assert (
            len(node_transitive_property_shapes)
            == s["number_of_direct_property_shapes"]
            + s["number_of_inherited_property_shapes"]
        )
        assert len(rdfcollection_items_to_remove) == len(s["parent_node_shapes"])
        assert len(triples_to_remove) == len(s["parent_node_shapes"])
        for parent_node in s["parent_node_shapes"]:
            assert (
                URIRef(s["shape"]),
                SH.node,
                URIRef(parent_node),
            ) in triples_to_remove


def test_import_transitive_closure(rdf_model_from_dir: RdfModel):
    assert len(rdf_model_from_dir.service._imported) == 0
    expected_schema_imports = []
    expected_ontology_imports = []
    for s in TYPES_SHAPES_MAP.values():
        _, _, _ = rdf_model_from_dir.service.get_shape_graph(URIRef(s["shape"]))
        assert URIRef(s["schema"]) in rdf_model_from_dir.service._imported
        s_schema_imports = [URIRef(imp) for imp in s["imports"]["schema"]]
        s_ontology_imports = [URIRef(imp) for imp in s["imports"]["ontology"]]
        if s_ontology_imports:
            assert (
                URIRef(s["schema"])
                in rdf_model_from_dir.service._defining_resource_to_imported_ontology
            )
            assert sorted(s_ontology_imports) == sorted(
                rdf_model_from_dir.service._defining_resource_to_imported_ontology[
                    URIRef(s["schema"])
                ]
            )
        s_imports = s_schema_imports + s_ontology_imports
        if s_imports:
            assert set(s_imports).issubset(rdf_model_from_dir.service._imported)
        expected_schema_imports.extend(s_schema_imports)
        expected_ontology_imports.extend(s_ontology_imports)

    expected_schema = [URIRef(val["schema"]) for val in TYPES_SHAPES_MAP.values()]
    assert len(rdf_model_from_dir.service._imported) == len(
        set(expected_schema + expected_schema_imports + expected_ontology_imports)
    )
    assert sorted(
        list(rdf_model_from_dir.service._defining_resource_to_imported_ontology.keys())
    ) == sorted(
        [URIRef("http://shapes.ex/employee"), URIRef("http://shapes.ex/person")]
    )
    assert len(
        rdf_model_from_dir.service._defining_resource_to_imported_ontology.values()
    ) == len(expected_ontology_imports)


def test_get_unknown_shape_graph_exception(rdf_model_from_dir: RdfModel):
    with pytest.raises(ValueError):
        shape, schema_graph, ont_graph = rdf_model_from_dir.service.get_shape_graph(
            URIRef("https://noshape")
        )


def test_get_shape_uriref_from_class_fragment(rdf_model_from_dir):
    for t, v in TYPES_SHAPES_MAP.items():
        shape_uriref = rdf_model_from_dir.service.get_shape_uriref_from_class_fragment(
            t
        )
        assert shape_uriref == URIRef(v["shape"])
