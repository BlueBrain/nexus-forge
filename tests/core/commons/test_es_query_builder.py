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
from typing import List

import elasticsearch_dsl
import pytest
from elasticsearch_dsl import Text, Keyword, Nested, Object, Integer, Q


from kgforge.core.commons.es_query_builder import (
    _recursive_resolve_nested,
    _build_keyword_path,
    _detect_mapping_type,
    ESQueryBuilder,
)
from kgforge.core.wrappings import Filter


class TestESQueryBuilder:
    @pytest.mark.parametrize(
        "property_path, mapping_type, dynamic_mapping_type, default_str_keyword_field, keyword_path",
        [
            pytest.param(
                ("annotation.hasBody.label"),
                (Text(fields={"keyword": Keyword()})),
                (None),
                (None),
                ("annotation.hasBody.label.keyword"),
                id="text_keyword_field",
            ),
            pytest.param(
                ("@type"),
                (Keyword()),
                (None),
                (None),
                ("@type"),
                id="keyword_field_path",
            ),
            pytest.param(
                ("objectOfStudy.label"),
                (Text()),
                (None),
                (None),
                (None),
                id="non_keyword_field",
            ),
            pytest.param(
                ("brainLocation.brainRegion"),
                (Object()),
                (None),
                (None),
                (None),
                id="object_field_path",
            ),
            pytest.param(
                ("contribution.agent.type"),
                (None),
                (Text()),
                ("keyword"),
                ("contribution.agent.type.keyword"),
                id="dynamic_mapping_type",
            ),
            pytest.param(
                ("contribution.agent.type"),
                (None),
                (None),
                ("keyword"),
                (None),
                id="noat_mapping_type",
            ),
        ],
    )
    def test__build_keyword_path(
        self,
        property_path,
        mapping_type,
        dynamic_mapping_type,
        default_str_keyword_field,
        keyword_path,
    ):
        k_p = _build_keyword_path(
            mapping_type, property_path, dynamic_mapping_type, default_str_keyword_field
        )
        assert k_p == keyword_path

    @pytest.mark.parametrize(
        "field_path, nested_path, found_path, mapping_type",
        [
            pytest.param(
                (["annotation", "hasBody", "label"]),
                (["annotation.hasBody"]),
                (["annotation","hasBody", "label"]),
                (Text(fields={"keyword": Keyword()})),
                id="text_keyword_field_in_nested",
            ),
            pytest.param(
                (["annotation", "hasBody"]),
                (["annotation.hasBody"]),
                (["annotation","hasBody"]),
                (Nested()),
                id="nested_field",
            ),
            pytest.param(
                (["annotation", "hasBody", "isMeasurementOf", "label"]),
                (["annotation.hasBody"]),
                (["annotation","hasBody"]),
                (Nested()),
                id="non_existing_field_in_nested",
            ),
            pytest.param(
                (["brainLocation", "brainRegion"]),
                ([]),
                (["brainLocation","brainRegion"]),
                (Object()),
                id="object_field"
            ),
            pytest.param(
                (["brainLocation", "brainRegion", "label"]),
                ([]),
                (["brainLocation", "brainRegion", "label"]),
                (Text(fields={"keyword": Keyword()})),
                id="text_keyword_field_in_object",
            ),
            pytest.param(
                (["an_integer"]),
                ([]),
                (["an_integer"]),
                (Integer(fields={"keyword": Keyword()})),
                id="integer_field",
            ),
            pytest.param((["@type"]), ([]), (["@type"]), (Keyword()), id="keyword_field"),
        ],
    )
    def test__recursive_resolve_nested(
        self, field_path, nested_path, found_path, mapping_type, es_mapping_dict
    ):
        es_mapping = elasticsearch_dsl.Mapping()
        es_mapping._update_from_dict(es_mapping_dict)
        n_p, f_p, m_t = _recursive_resolve_nested(es_mapping, field_path)
        assert n_p == nested_path
        assert f_p == found_path
        assert str(m_t) == str(mapping_type)

    @pytest.mark.parametrize(
        "value, mapping_type",
        [
            pytest.param(
                ("A str value"), (elasticsearch_dsl.Text()), id="text_mapping_type"
            ),
            pytest.param(
                ("2020-10-20T13:53:22.880Z"),
                (elasticsearch_dsl.Date()),
                id="date_mapping_type",
            ),
            pytest.param((3), (elasticsearch_dsl.Long()), id="integer_mapping_type"),
            pytest.param(
                ("8.2"), (elasticsearch_dsl.Float()), id="str_double_mapping_type"
            ),
            pytest.param(
                (True), (elasticsearch_dsl.Boolean()), id="true_bool_mapping_type"
            ),
            pytest.param(
                (False), (elasticsearch_dsl.Boolean()), id="false_bool_mapping_type"
            ),
        ],
    )
    def test__detect_mapping_type(self, value, mapping_type):
        m_t = _detect_mapping_type(value)
        assert str(m_t) == str(mapping_type)

    @pytest.mark.parametrize(
        "filters, params, es_query",
        [
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["annotation", "hasBody", "label"],
                            value="An annotation",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().filter(
                        "nested",
                        path="annotation.hasBody",
                        query=elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Q(
                                    "term",
                                    **{
                                        "annotation.hasBody.label.keyword": "An annotation"
                                    },
                                )
                            ]
                        ),
                    )
                ),
                id="build_nested_filter_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["annotation", "hasBody", "isMeasurementOf"],
                            value="An annotation",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        "bool",
                        must=[
                            elasticsearch_dsl.query.Nested(
                                path="annotation.hasBody",
                                query=elasticsearch_dsl.query.Bool(
                                    must=[
                                        elasticsearch_dsl.query.Q(
                                            "match",
                                            **{
                                                "annotation.hasBody.isMeasurementOf": "An annotation"
                                            },
                                        )
                                    ]
                                ),
                            ).to_dict()
                        ],
                    )
                    # )
                ),
                id="build_unknown_nested_must_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["brainLocation", "brainRegion", "label"],
                            value="A label",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Term(
                                    **{
                                        "brainLocation.brainRegion.label.keyword": "A label"
                                    }
                                )
                            ]
                        )
                    )
                ),
                id="build_filter_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["brainLocation", "layer", "label"],
                            value="A label",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            must=[
                                elasticsearch_dsl.query.Match(
                                    **{"brainLocation.layer.label": "A label"}
                                )
                            ]
                        )
                    )
                ),
                id="build_match_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["brainLocation", "brainRegion", "isDefinedBy"],
                            value="A definition",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Term(
                                    **{
                                        "brainLocation.brainRegion.isDefinedBy.keyword": "A definition"
                                    }
                                )
                            ]
                        )
                    )
                ),
                id="build_unknown_filter_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__ne__",
                            path=["brainLocation", "brainRegion", "label"],
                            value="A label",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            must_not=[
                                elasticsearch_dsl.query.Term(
                                    **{
                                        "brainLocation.brainRegion.label.keyword": "A label"
                                    }
                                )
                            ]
                        )
                    )
                ),
                id="build_must_not_filter_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__ne__",
                            path=["brainLocation", "layer", "label"],
                            value="A label",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            must_not=[
                                elasticsearch_dsl.query.Match(
                                    **{"brainLocation.layer.label": "A label"}
                                )
                            ]
                        )
                    )
                ),
                id="build_must_not_match_query",
            ),
            pytest.param(
                ([Filter(operator="__gt__", path=["an_integer"], value="3")]),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Range(
                                    **{"an_integer": {"gt": "3"}}
                                )
                            ]
                        )
                    )
                ),
                id="build_range_gt_query",
            ),
            pytest.param(
                ([Filter(operator="__le__", path=["series", "a_float"], value="2.0")]),
                ({}),
                (
                    elasticsearch_dsl.Search().filter(
                        "nested",
                        path="series",
                        query=elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Range(
                                    **{"series.a_float": {"lte": "2.0"}}
                                )
                            ]
                        ),
                    )
                ),
                id="build_range_le_nested_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["unknown", "path"],
                            value="Unknown value",
                        )
                    ]
                ),
                ({"default_str_keyword_field": "keyword"}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Term(
                                    **{"unknown.path.keyword": "Unknown value"}
                                )
                            ]
                        )
                    )
                ),
                id="build_complete_unknown_path_filter_text",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["unknown", "path"],
                            value="Unknown value",
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Term(
                                    **{"unknown.path.keyword": "Unknown value"}
                                )
                            ]
                        )
                    )
                ),
                id="build_complete_unknown_path_filter_text_no_default_str_keyword_field",
            ),
            pytest.param(
                ([Filter(operator="__eq__", path=["unknown", "path"], value="3.0")]),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Bool(
                            must=[
                                elasticsearch_dsl.query.Match(**{"unknown.path": "3.0"})
                            ]
                        )
                    )
                ),
                id="build_complete_unknown_path_must_match_float",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["a_dense_vector"],
                            value=[0.1, 0.3, 0.8],
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.ScriptScore(
                            query=elasticsearch_dsl.query.Bool(
                                must=[
                                    elasticsearch_dsl.query.Exists(
                                        field="a_dense_vector"
                                    )
                                ]
                            ),
                            script={
                                "source": "doc['a_dense_vector'].size() == 0 ? 0 : (cosineSimilarity(params.queryVector, doc['a_dense_vector'])+1.0) / 2",
                                "params": {"queryVector": [0.1, 0.3, 0.8]},
                            },
                        )
                    )
                ),
                id="build_dense_vector_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["derivation", "a_dense_vector"],
                            value=[0.1, -0.3, 0.8],
                        )
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        elasticsearch_dsl.query.Nested(
                            path="derivation",
                            query=elasticsearch_dsl.query.ScriptScore(
                                query=elasticsearch_dsl.query.Bool(
                                    must=[
                                        elasticsearch_dsl.query.Exists(
                                            field="derivation.a_dense_vector"
                                        )
                                    ]
                                ),
                                script={
                                    "source": "doc['derivation.a_dense_vector'].size() == 0 ? 0 : (cosineSimilarity(params.queryVector, doc['derivation.a_dense_vector'])+1.0) / 2",
                                    "params": {"queryVector": [0.1, -0.3, 0.8]},
                                },
                            ),
                        )
                    )
                ),
                id="build_nested_dense_vector_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["brainLocation", "brainRegion", "label"],
                            value="A label",
                        )
                    ]
                ),
                ({"includes": ["to_include"], "excludes": ["to_exclude"]}),
                (
                    elasticsearch_dsl.Search()
                    .query(
                        elasticsearch_dsl.query.Bool(
                            filter=[
                                elasticsearch_dsl.query.Term(
                                    **{
                                        "brainLocation.brainRegion.label.keyword": "A label"
                                    }
                                )
                            ]
                        )
                    )
                    .source(includes=["to_include"], excludes=["to_exclude"])
                ),
                id="build_query_with_source",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["type", "id"],
                            value="Dataset",
                        ),
                        Filter(
                            operator="__eq__",
                            path=["contribution", "agent", "type"],
                            value="Person",
                        ),
                        Filter(
                            operator="__eq__",
                            path=["contribution", "agent", "id"],
                            value="https://orcid",
                        ),
                        Filter(
                            operator="__ne__",
                            path=["derivation", "entity", "@type"],
                            value="Entity",
                        ),
                    ]
                ),
                ({}),
                (
                    elasticsearch_dsl.Search().query(
                        "bool",
                        filter=[
                            elasticsearch_dsl.query.Term(
                                **{
                                    "@type": "Dataset"
                                }
                            ).to_dict(),
                            elasticsearch_dsl.query.Nested(
                                path="contribution.agent",
                                query=elasticsearch_dsl.query.Bool(
                                    filter=[
                                        elasticsearch_dsl.query.Term(
                                            **{
                                                "contribution.agent.@type.keyword": "Person"
                                            }
                                        )
                                    ]
                                ),
                            ).to_dict(),
                            elasticsearch_dsl.query.Nested(
                                path="contribution.agent",
                                query=elasticsearch_dsl.query.Bool(
                                    filter=[
                                        elasticsearch_dsl.query.Term(
                                            **{
                                                "contribution.agent.@id": "https://orcid"
                                            }
                                        )
                                    ]
                                ),
                            ).to_dict(),
                        ],
                        must_not=[
                            elasticsearch_dsl.query.Nested(
                                path="derivation.entity",
                                query=elasticsearch_dsl.query.Bool(
                                    must_not=[
                                        elasticsearch_dsl.query.Term(
                                            **{
                                                "derivation.entity.@type.keyword": "Entity"
                                            }
                                        )
                                    ]
                                ),
                            ).to_dict()
                        ],
                    )
                ),
                id="rewrite_type_id",
            ),
        ],
    )
    def test_build(self, filters, params, es_query, es_mapping_dict):
        es_mapping = elasticsearch_dsl.Mapping()
        es_mapping._update_from_dict(es_mapping_dict)
        query = ESQueryBuilder.build(es_mapping_dict, None, None, filters, **params)
        assert isinstance(query, dict)
        assert elasticsearch_dsl.Search.from_dict(query) == es_query

    @pytest.mark.parametrize(
        "filters, default_str_keyword_field",
        [
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["brainLocation", "brainRegion"],
                            value="A brainRegion",
                        )
                    ]
                ),
                (None),
                id="build_failing_object_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__gt__",
                            path=["brainLocation", "brainRegion", "label"],
                            value="A label",
                        )
                    ]
                ),
                (None),
                id="build_failing_gt_Text_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__ge__",
                            path=["annotation", "hasBody", "label"],
                            value="A label",
                        )
                    ]
                ),
                (None),
                id="build_failing_ge_nested_Text_query",
            ),
            pytest.param(
                ([Filter(operator="__lt__", path=["a_boolean"], value="A boolean")]),
                (None),
                id="build_failing_lt_Boolean_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__lt__",
                            path=["a_dense_vector"],
                            value=[0.1, 0.3, 0.8],
                        )
                    ]
                ),
                (None),
                id="build_failing_dense_vector_query",
            ),
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["a_dense_vector"],
                            value=[0.1, 0.3, 0.8],
                        ),
                        Filter(
                            operator="__eq__",
                            path=["a_dense_vector"],
                            value=[0.5, 0.5, 0.9],
                        ),
                    ]
                ),
                (None),
                id="build_failing_multiple_dense_vector_query",
            ),
        ],
    )
    def test_build_exception(self, filters, default_str_keyword_field, es_mapping_dict):
        es_mapping = elasticsearch_dsl.Mapping()
        es_mapping._update_from_dict(es_mapping_dict)

        with pytest.raises(ValueError):
            ESQueryBuilder.build(
                es_mapping_dict,
                None,
                None,
                filters,
                default_str_keyword_field=default_str_keyword_field,
            )

    @pytest.mark.parametrize(
        "filters, default_str_keyword_field",
        [
            pytest.param(
                (
                    [
                        Filter(
                            operator="__eq__",
                            path=["annotation", "hasBody", "isMeasurementOf"],
                            value="An annotation",
                        )
                    ]
                ),
                (None),
                id="build_nested_filter_query",
            )
        ],
    )
    def test_build_dynamic_false(
        self, filters, default_str_keyword_field, es_mapping_dict
    ):
        es_mapping = elasticsearch_dsl.Mapping()
        es_mapping._update_from_dict(es_mapping_dict)

        with pytest.raises(ValueError):
            es_mapping_dict["dynamic"] = False
            ESQueryBuilder.build(
                es_mapping_dict,
                None,
                None,
                filters,
                default_str_keyword_field=default_str_keyword_field,
            )
