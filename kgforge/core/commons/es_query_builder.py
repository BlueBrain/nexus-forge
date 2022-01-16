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
import copy

import datetime
import dateutil
import elasticsearch_dsl
from dateutil.parser import ParserError
from elasticsearch_dsl import Field
from typing import Tuple, List, Dict, Optional, Any

from kgforge.core.commons.context import Context
from kgforge.core.commons.query_builder import QueryBuilder
from kgforge.core.wrappings import Filter, FilterOperator

elasticsearch_operator_range_map = {
    FilterOperator.LOWER_THAN.value: "lt",
    FilterOperator.LOWER_OR_Equal_Than.value: "lte",
    FilterOperator.GREATER_Than.value: "gt",
    FilterOperator.GREATER_OR_Equal_Than.value: "gte",
}


class ESQueryBuilder(QueryBuilder):
    @staticmethod
    def build(
        schema: Dict,
        resolvers: Optional[List["Resolver"]],
        context: Context,
        *filters,
        **params,
    ) -> Tuple[List, List, List]:

        es_filters = list()
        musts = list()
        must_nots = list()
        script_scores = list()

        default_str_keyword_field = params.get("default_str_keyword_field", "keyword")
        includes = params.get("includes", None)
        excludes = params.get("excludes", None)

        m = elasticsearch_dsl.Mapping()
        dynamic = True
        if schema is not None:
            m._update_from_dict(schema)
            dynamic = m._meta["dynamic"] if "dynamic" in m._meta else dynamic

        for index, f in enumerate(*filters):
            _filter = None
            must = None
            must_not = None
            script_score = None
            last_path = f.path[-1]
            property_path = ".".join(f.path)
            found_path_parts = None
            nested_path, mapping_type = m.resolve_nested(field_path=property_path)
            if isinstance(mapping_type, elasticsearch_dsl.Nested) or isinstance(
                mapping_type, elasticsearch_dsl.Object
            ):
                raise ValueError(
                    f"The provided path {f.path} can't be used for filter/search because it is not a leaf property."
                )
            if (
                isinstance(mapping_type, elasticsearch_dsl.DenseVector)
                and f.operator != FilterOperator.EQUAL.value
            ):
                raise ValueError(
                    f"The provided DenseVector path '{f.path}' can't be used for filter/search but only with the "
                    f"'__eq__' operator for similarity search."
                )

            if mapping_type is None and nested_path == ():
                if not dynamic:
                    raise ValueError(
                        f"The provided path {f.path} is not present in the provided elasticsearch mapping (dynamic == {dynamic}). "
                        f"Please search with a path present in the elasticsearch mapping or provide a dynamic mapping."
                    )
                else:
                    (
                        nested_path,
                        found_path_parts,
                        mapping_type,
                    ), property_path = _look_up_known_parent_paths(
                        f, last_path, property_path, m
                    )
            # else (i.e mapping_type == Text, Keyword, ...) (i.e nested_path with value => in a nested field
            if len(nested_path) >= 1:
                keyword_path = _build_keyword_path(mapping_type, property_path)
                if keyword_path:
                    filter_or_must_or_must_not = (
                        "filter"
                        if f.operator == FilterOperator.EQUAL.value
                        else "must_not"
                    )
                    k_path = keyword_path
                    term_or_match = "term"
                else:
                    filter_or_must_or_must_not = (
                        "must"
                        if f.operator == FilterOperator.EQUAL.value
                        else "must_not"
                    )
                    k_path = property_path
                    term_or_match = "match"
                n_path = nested_path

            # nested_path = [] => (i.e mapping_type == Text, Date, Keyword, ...) - nested_path empty
            else:
                found_path = ".".join(found_path_parts) if found_path_parts else None
                if mapping_type is None or (found_path and found_path != property_path):
                    mapping_type = _detect_mapping_type(f.value)
                    keyword_path = _build_keyword_path(
                        None,
                        property_path,
                        dynamic_mapping_type=mapping_type,
                        default_str_keyword_field=default_str_keyword_field
                    )
                else:
                    keyword_path = _build_keyword_path(mapping_type, property_path)
                if keyword_path:
                    filter_or_must_or_must_not = (
                        "filter"
                        if f.operator == FilterOperator.EQUAL.value
                        else "must_not"
                    )
                    k_path = keyword_path
                    term_or_match = "term"
                else:
                    filter_or_must_or_must_not = (
                        "must"
                        if f.operator == FilterOperator.EQUAL.value
                        else "must_not"
                    )
                    k_path = property_path
                    term_or_match = "match"
                n_path = None

            _filter, must, must_not, script_score = _build_bool_query(
                f,
                mapping_type,
                k_path,
                property_path,
                filter_or_must_or_must_not,
                term_or_match,
                n_path,
            )

            if _filter:
                es_filters.append(_filter)
            if must:
                musts.append(must)
            if must_not:
                must_nots.append(must_not)
            if script_score:
                script_scores.append(script_score)

        if len(script_scores) > 1:
            raise ValueError(
                f"Multiple dense vector similarity query are not supported: {len(script_scores)} filters involving dense vectors were provided."
            )
        elif len(script_scores) == 1:
            bool_query = _wrap_in_bool_query(es_filters, musts, must_nots)
            return _wrap_in_script_score_query(
                bool_query, script_scores[0], includes, excludes
            )
        else:
            return _wrap_in_bool_query(es_filters, musts, must_nots, includes, excludes)


def _look_up_known_parent_paths(f, last_path, property_path, m):
    if (
        len(f.path) >= 2
        and last_path in ["id", "@id"]
        and f.path[-2] in ["type", "@type"]
    ):  # to cope with paths.type.id TODO: fix forge.paths to not add id after type
        property_path = _join_property_path(f.path[:-2], "@type")

    elif len(f.path) >= 1 and last_path in ["type", "@type"]:
        property_path = _join_property_path(f.path[:-1], "@type")

    elif len(f.path) >= 1 and last_path in ["id", "@id"]:
        property_path = _join_property_path(f.path[:-1], "@id")

    parts = property_path.split(".")
    return _recursive_resolve_nested(m, parts), property_path


def _join_property_path(f_path, to_join_with):
    property_path = ".".join(f_path)
    property_path = (
        property_path + "." + to_join_with if property_path != "" else to_join_with
    )
    return property_path


def _wrap_in_bool_query(filters, musts, must_nots, includes=None, excludes=None):
    bool_query = {
        "query": {"bool": {"filter": filters, "must": musts, "must_not": must_nots}}
    }
    return _add_source(bool_query, includes, excludes)


def _wrap_in_script_score_query(query, script, includes=None, excludes=None):
    # Todo: Catch non supported combination of nested query and non nested ones
    if isinstance(script, elasticsearch_dsl.query.Nested):
        script.query = elasticsearch_dsl.query.ScriptScore(
            query=query["query"], script=script.query.to_dict()["script"]
        )
        script_score_query = script
    else:
        script_score_query = elasticsearch_dsl.query.ScriptScore(
            query=query["query"], script=script.to_dict()["script"]
        )
    query = elasticsearch_dsl.Search().query(script_score_query.to_dict()).to_dict()
    return _add_source(query, includes, excludes)


def _add_source(query, includes, excludes):
    _source = {}
    if includes:
        _source["includes"] = includes
    if excludes:
        _source["excludes"] = excludes
    if _source:
        query_copy = copy.deepcopy(query)
        query_copy["_source"] = _source
        return query_copy
    else:
        return query


def _recursive_resolve_nested(m, field_path):
    nested_path, mapping_type = m.resolve_nested(field_path=".".join(field_path))
    if mapping_type is None and nested_path == ():
        if len(field_path) > 1:
            return _recursive_resolve_nested(
                m, field_path=field_path[0 : len(field_path) - 1]
            )
        else:
            return nested_path, field_path, mapping_type

    else:
        return nested_path, field_path, mapping_type


def _build_keyword_path(
    mapping_type,
    property_path,
    dynamic_mapping_type=None,
    default_str_keyword_field=None,
):
    if isinstance(mapping_type, elasticsearch_dsl.Keyword):
        keyword_path = property_path
    elif (
        mapping_type is None
        and default_str_keyword_field is not None
        and isinstance(dynamic_mapping_type, elasticsearch_dsl.Text)
    ):
        keyword_path = ".".join([property_path, default_str_keyword_field])
    elif mapping_type is not None:
        keyword_fields = [
            keyword_field
            for keyword_field, val in mapping_type.fields.to_dict().items()
            if isinstance(val, elasticsearch_dsl.Keyword)
        ]
        keyword_path = (
            ".".join([property_path, keyword_fields[0]])
            if len(keyword_fields) >= 1
            else None
        )
    else:
        keyword_path = None
    return keyword_path


def _build_bool_query(
    filter: Filter,
    mapping_type: Field,
    k_path: str,
    property_path: str,
    filter_or_must_or_must_not: str,
    term_or_match: str,
    nested_path: List[str] = None,
):
    _filter = None
    must = None
    must_not = None
    script_score = None
    if (
        filter.operator in elasticsearch_operator_range_map.keys()
        and not isinstance(mapping_type, elasticsearch_dsl.Text)
        and not isinstance(mapping_type, elasticsearch_dsl.Boolean)
    ):  # range filter query
        if nested_path:
            _filter = _wrap_in_nested_bool_query(
                nested_path[-1],
                "filter",
                "range",
                {
                    property_path: {
                        elasticsearch_operator_range_map[filter.operator]: filter.value
                    }
                },
            )
        else:
            _filter = _wrap_in_non_nested_query_query(
                property_path,
                "range",
                {elasticsearch_operator_range_map[filter.operator]: filter.value},
            )

    elif filter.operator in elasticsearch_operator_range_map.keys() and (
        isinstance(mapping_type, elasticsearch_dsl.Text)
        or isinstance(mapping_type, elasticsearch_dsl.Boolean)
    ):
        raise ValueError(
            f"Using the range operator {filter.operator} on the Text field/path {filter.path} is not supported."
        )
    elif filter.operator == FilterOperator.EQUAL.value and isinstance(
        mapping_type, elasticsearch_dsl.DenseVector
    ):
        if nested_path:
            sim_query = _wrap_in_script_query(k_path, filter.value)
            script_score = _wrap_in_nested_query(
                path=nested_path[-1], query=sim_query.to_dict()
            )
        else:
            script_score = _wrap_in_script_query(k_path, filter.value)

        must = _wrap_in_non_nested_query_query(
            "field", "exists", k_path
        )  # otherwise script_score will fail. This will be added in a nested script_score query
    else:
        if nested_path:
            query = _wrap_in_nested_bool_query(
                nested_path[-1],
                filter_or_must_or_must_not,
                term_or_match,
                {k_path: filter.value},
            )
        else:
            query = _wrap_in_non_nested_query_query(k_path, term_or_match, filter.value)

        if filter_or_must_or_must_not == "filter":
            _filter = query
        elif filter_or_must_or_must_not == "must":
            must = query
        else:
            must_not = query
    return _filter, must, must_not, script_score


def _wrap_in_nested_bool_query(
    path, filter_or_must_or_must_not, filter_type, filter_value
):
    return _wrap_in_nested_query(
        path=path,
        query=elasticsearch_dsl.query.Q(
            "bool",
            **{
                filter_or_must_or_must_not: elasticsearch_dsl.query.Q(
                    filter_type, **filter_value
                ).to_dict()
            },
        ),
    ).to_dict()


def _wrap_in_nested_query(path: str, query: Dict):
    return elasticsearch_dsl.query.Nested(path=path, query=query)


def _detect_mapping_type(value: Any):

    try:
        # integer
        if str(value).isnumeric():
            return elasticsearch_dsl.Long()
        # bool
        if value is True or value is False:
            return elasticsearch_dsl.Boolean()
        # double
        if float(value):
            return elasticsearch_dsl.Float()
    except ValueError as ve:
        pass
    except TypeError as te:
        pass
    try:
        # Date
        if isinstance(dateutil.parser.parse(str(value)), datetime.datetime):
            return elasticsearch_dsl.Date()
    except ParserError as pe:
        return elasticsearch_dsl.Text()


def _wrap_in_non_nested_query_query(path, filter_type, filter_value):
    query = {filter_type: {path: filter_value}}
    return query


def _wrap_in_script_query(field: str, queryVector: List):
    return elasticsearch_dsl.query.Script(
        source=f"doc['{field}'].size() == 0 ? 0 : (cosineSimilarity(params.queryVector, doc['{field}'])+1.0) / 2",
        params={"queryVector": queryVector},
    )
