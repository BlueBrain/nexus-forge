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

from datetime import datetime
from enum import Enum
import json
from pyld import jsonld
import rdflib
import re
from rdflib import Graph
from rdflib.plugins.sparql.parser import Query
from typing import Any, Dict, List, Match, Optional, Tuple, Union, Type, Pattern

from kgforge.core.commons.exceptions import QueryingError
from kgforge.core.resource import Resource
from kgforge.core.conversions.rdf import from_jsonld
from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.commons.context import Context
from kgforge.core.commons.files import is_valid_url
from kgforge.core.commons.parser import _parse_type, _process_types
from kgforge.core.commons.query_builder import QueryBuilder
from kgforge.core.wrappings.paths import Filter


class CategoryDataType(Enum):
    DATETIME = "datetime"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LITERAL = "literal"


# FIXME: need to find a comprehensive way (different than list) to get all SPARQL reserved clauses


SPARQL_CLAUSES = [
    "where",
    "filter",
    "select",
    "union",
    "limit",
    "construct",
    "optional",
    "bind",
    "values",
    "offset",
    "order by",
    "prefix",
    "graph",
    "distinct",
    "in",
    "as",
    "base",
    "prefix",
    "reduced",
    "describe",
    "ask",
    "named",
    "asc",
    "desc",
    "from",
    "optional",
    "graph",
    "regex",
    "union",
    "str",
    "lang",
    "langmatches",
    "datatype",
    "bound",
    "sameTerm",
    "isIRI",
    "isURI",
    "isBLANK",
    "isLITERAL",
    "group",
    "by",
    "order",
    "minus",
    "not",
    "exists",
]

type_map = {
    datetime: CategoryDataType.DATETIME,
    str: CategoryDataType.LITERAL,
    bool: CategoryDataType.BOOLEAN,
    int: CategoryDataType.NUMBER,
    float: CategoryDataType.NUMBER,
    complex: CategoryDataType.NUMBER,
}

format_type = {
    CategoryDataType.DATETIME: lambda x: f'"{x}"^^xsd:dateTime',
    CategoryDataType.NUMBER: lambda x: x,
    CategoryDataType.LITERAL: lambda x: f'"{x}"',
    CategoryDataType.BOOLEAN: lambda x: (
        "'true'^^xsd:boolean" if x else "'false'^^xsd:boolean"
    ),
}

sparql_operator_map = {
    "__lt__": "<",
    "__le__": "<=",
    "__eq__": "=",
    "__ne__": "!=",
    "__gt__": ">",
    "__ge__": ">=",
}


class SPARQLQueryBuilder(QueryBuilder):

    @staticmethod
    def build(
        schema: Optional[Dict],
        resolvers: Optional[List[Resolver]],
        context: Context,
        filters: List[Filter],
        **params,
    ) -> Tuple[List, List]:

        statements = []
        sparql_filters = []
        for index, f in enumerate(filters):
            last_path = f.path[-1]
            try:
                last_term = context.terms[last_path]
            except KeyError:
                last_term = None
            if last_path in ["id", "@id"]:
                property_path = "/".join(f.path[:-1])
            elif last_path == "@type":
                minus_last_path = f.path[:-1]
                minus_last_path.append("type")
                property_path = "/".join(minus_last_path)
            else:
                property_path = "/".join(f.path)
            try:
                if (
                    last_path in ["type", "@type"]
                    or last_path in ["id", "@id"]
                    or (last_term is not None and last_term.type == "@id")
                ):
                    if f.operator == "__eq__":
                        statements.append(
                            f"{property_path} {_box_value_as_full_iri(f.value)}"
                        )
                    elif f.operator == "__ne__":
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(f"FILTER(?v{index} != {f.value})")
                    else:
                        raise NotImplementedError(
                            "supported operators are '==' and '!=' when filtering by type or id."
                        )
                else:
                    parsed_type, parsed_value = _parse_type(f.value, parse_str=False)
                    value_type = type_map[parsed_type]
                    value = format_type[value_type](
                        parsed_value if parsed_value else f.value
                    )
                    if value_type is CategoryDataType.LITERAL:
                        if f.operator not in ["__eq__", "__ne__"]:
                            raise NotImplementedError(
                                "supported operators are '==' and '!=' when filtering with a str."
                            )
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(
                            f"FILTER(?v{index} = {_box_value_as_full_iri(value)})"
                        )
                    else:
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(
                            f"FILTER(?v{index} {sparql_operator_map[f.operator]} {_box_value_as_full_iri(value)})"
                        )
            except NotImplementedError as nie:
                raise ValueError(
                    f"Operator '{sparql_operator_map[f.operator]}' "
                    f"is not supported with the value '{f.value}': {str(nie)}"
                ) from nie
        return statements, sparql_filters

    @staticmethod
    def build_resource_from_response(
        query: str, response: Dict, context: Context, *args, **params
    ) -> List[Resource]:
        _, q_comp = Query.parseString(query)
        bindings = response["results"]["bindings"]
        # FIXME workaround to parse a CONSTRUCT query, this fix depends on
        #  https://github.com/BlueBrain/nexus/issues/1155
        if q_comp.name == "ConstructQuery":
            return SPARQLQueryBuilder.build_resource_from_construct_query(
                bindings, context
            )

        # SELECT QUERY
        return SPARQLQueryBuilder.build_resource_from_select_query(bindings)

    @staticmethod
    def build_resource_from_construct_query(
        results: List, context: Context
    ) -> List[Resource]:

        subject_triples = {}

        for r in results:
            subject = r["subject"]["value"]
            s = f"<{r['subject']['value']}>"
            p = f"<{r['predicate']['value']}>"
            if r["object"]["type"] == "uri":
                o = f"<{r['object']['value']}>"
            else:
                if "datatype" in r["object"]:
                    o = f"\"{r['object']['value']}\"^^<{r['object']['datatype']}>"
                else:
                    o = f"\"{r['object']['value']}\""
            if subject in subject_triples:
                subject_triples[subject] += f"\n{s} {p} {o} . "
            else:
                subject_triples[subject] = f"{s} {p} {o} . "

        def triples_to_resource(iri, triples):
            graph = Graph().parse(data=triples, format="nt")
            data_expanded = json.loads(graph.serialize(format="json-ld"))
            data_framed = jsonld.frame(data_expanded, {"@id": iri})
            compacted = jsonld.compact(data_framed, context.document)
            resource = from_jsonld(compacted)
            resource.context = (
                context.iri if context.is_http_iri() else context.document["@context"]
            )
            return resource

        return [triples_to_resource(s, t) for s, t in subject_triples.items()]

    @staticmethod
    def build_resource_from_select_query(results: List) -> List[Resource]:

        def process_v(v):
            if (
                v["type"] == "literal"
                and "datatype" in v
                and v["datatype"] == "http://www.w3.org/2001/XMLSchema#boolean"
            ):

                return json.loads(str(v["value"]).lower())

            elif (
                v["type"] == "literal"
                and "datatype" in v
                and v["datatype"] == "http://www.w3.org/2001/XMLSchema#integer"
            ):

                return int(v["value"])

            else:
                return v["value"]

        return [Resource(**{k: process_v(v) for k, v in x.items()}) for x in results]

    @staticmethod
    def rewrite_sparql(
        query: str,
        # context: Context, metadata_context: Context,
        context_as_dict: Dict,
        prefixes: Optional[Dict],
        vocab: Optional[str],
    ) -> str:
        """Rewrite local property and type names from Model.template() as IRIs.

        Local names are mapped to IRIs by using a JSON-LD context, i.e. { "@context": { ... }}
        from a kgforge.core.commons.Context.
        In the case of contexts using prefixed names, prefixes are added to the SPARQL query prologue.
        In the case of non-available contexts and vocab then the query is returned unchanged.
        """

        has_prefixes = prefixes is not None and len(prefixes.keys()) > 0
        has_vocab = vocab is not None

        if context_as_dict.get("type") == "@type":
            context_as_dict["type"] = (
                "rdf:type"
                if "rdf" in prefixes
                else "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            )

        def replace(match: Match) -> str:
            m4 = match.group(4)
            if m4 is None:
                return match.group(0)
            else:
                v = (
                    context_as_dict.get(m4, ":" + m4 if has_vocab else None)
                    if str(m4).lower() not in SPARQL_CLAUSES
                    and not str(m4).startswith("https")
                    else m4
                )
                if v is None:
                    raise QueryingError(
                        f"Failed to construct a valid SPARQL query: add '{m4}'"
                        f", define an @vocab in the configured JSON-LD context or "
                        f"provide a fully correct SPARQL query."
                    )
                m5 = match.group(5)
                if "//" in v:
                    return f"<{v}>{m5}"
                else:
                    return f"{v}{m5}"

        g4 = r"([a-zA-Z_]+)"
        g5 = r"([.;]?)"
        g0 = rf"((?<=[\s,[(/|!^])((a|true|false)|{g4}){g5}(?=[\s,\])/|?*+]))"
        g6 = r"(('[^']+')|('''[^\n\r]+''')|(\"[^\"]+\")|(\"\"\"[^\n\r]+\"\"\"))"
        rx = rf"{g0}|{g6}|(?<=< )(.*)(?= >)"
        qr = re.sub(rx, replace, query, flags=re.VERBOSE | re.MULTILINE)

        if not has_prefixes or "prefix" in str(qr).lower():
            return qr

        pfx = "\n".join(f"PREFIX {k}: <{v}>" for k, v in prefixes.items())

        if has_vocab:
            pfx = "\n".join([pfx, f"PREFIX : <{vocab}>"])

        return f"{pfx}\n{qr}"

    @staticmethod
    def _replace_in_sparql(
        qr: str,
        what: str,
        value: Optional[int],
        default_value: int,
        search_regex: Pattern,
        replace_if_in_query=True,
    ) -> str:

        is_what_in_query = bool(re.search(pattern=search_regex, string=qr))

        replace_value = (
            f" {what} {value}"
            if value
            else (f" {what} {default_value}" if default_value else None)
        )

        if is_what_in_query:
            if not replace_if_in_query and value:
                raise QueryingError(
                    f"Value for '{what}' is present in the provided query and set as argument: "
                    f"set 'replace_if_in_query' to True to replace '{what}' when present in the query."
                )

            if replace_if_in_query and replace_value:
                qr = re.sub(pattern=search_regex, repl=replace_value, string=qr)
        else:
            if replace_value:
                qr = f"{qr} {replace_value}"  # Added to the end of the query (not very general)

        return qr

    @staticmethod
    def apply_limit_and_offset_to_query(
        query, limit, default_limit, offset, default_offset
    ):
        if limit:
            query = SPARQLQueryBuilder._replace_in_sparql(
                query,
                "LIMIT",
                limit,
                default_limit,
                re.compile(r" LIMIT \d+", flags=re.IGNORECASE),
            )
        if offset:
            query = SPARQLQueryBuilder._replace_in_sparql(
                query,
                "OFFSET",
                offset,
                default_offset,
                re.compile(r" OFFSET \d+", flags=re.IGNORECASE),
            )

        return query

    @staticmethod
    def create_select_query(
        vars_: List[str],
        statements: Union[str, List[str]],
        distinct: bool,
        search_in_graph: bool,
        union: bool = False,
    ):
        if not union:
            all_statements = (
                ". ".join(statements) if isinstance(statements, list) else statements
            )

        elif not isinstance(statements, list):
            raise AttributeError(
                f"Expected statements argument to be of type  List[str] when union is True. Each item will go in a UNION clause: {statements}"
            )
        else:
            all_statements = "}} UNION {{".join(statements)
            all_statements = "{{" + all_statements + "}}"

        where_clauses = (
            f"{{ Graph ?g {{{all_statements}}}}}"
            if search_in_graph
            else f"{{{all_statements}}}"
        )

        join_vars_ = " ".join(vars_)
        select_vars = f"DISTINCT {join_vars_}" if distinct else f"{join_vars_}"
        return f"SELECT {select_vars} WHERE {where_clauses}"


def _box_value_as_full_iri(value):
    return f"<{value}>" if is_valid_url(value) else value


def build_shacl_query(
    statements: List[str] = None,
    defining_property_uri: str = None,
    deprecated_property_uri: str = None,
    deprecated: bool = False,
    deprecated_optional: bool = False,
    search_in_graph: bool = False,
    context: Context = None,
) -> str:
    deprecated_statement = (
        f"?resource_id <{deprecated_property_uri}> '{str(deprecated).lower()}'^^xsd:boolean"
        if deprecated_property_uri
        else ""
    )
    defining_statement = (
        f"?resource_id <{defining_property_uri}> ?shape"
        if defining_property_uri
        else ""
    )
    if deprecated_optional and deprecated_property_uri:
        deprecated_statement = " OPTIONAL {" + deprecated_statement + "}"
    shape_target_statement = "?shape sh:targetClass ?type"
    extra_statements = [defining_statement, deprecated_statement]
    if statements:
        extra_statements.extend(statements)
    shape_target_statement_str = ".".join([shape_target_statement] + extra_statements)
    shape_node_statements_str = (
        "SELECT (?shape as ?type) ?shape ?resource_id WHERE { ?shape a sh:NodeShape ."
        + "?shape a rdfs:Class . {}".format(".".join(extra_statements) + "}")
    )
    shape_node_not_targeting_statements_str = (
        "SELECT ?shape ?resource_id WHERE { ?shape a sh:NodeShape ."
        + "FILTER NOT EXISTS {?shape sh:targetClass []} FILTER NOT EXISTS {?shape a rdfs:Class}"
        + " . {}".format(".".join(extra_statements) + "}")
    )
    all_statements = [
        shape_target_statement_str,
        shape_node_statements_str,
        shape_node_not_targeting_statements_str,
    ]
    vars_ = ["?type", "?shape", "?resource_id"]
    if search_in_graph:
        vars_.append("?g")
    shacl_query = SPARQLQueryBuilder.create_select_query(
        vars_=vars_,
        statements=all_statements,
        distinct=True,
        search_in_graph=search_in_graph,
        union=True,
    )
    if not context:
        return shacl_query
    else:
        return SPARQLQueryBuilder.rewrite_sparql(
            shacl_query,
            context_as_dict=context.document,
            prefixes=context.prefixes,
            vocab=context.vocab,
        )


def build_ontology_query() -> str:
    query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            SELECT DISTINCT ?ont ?g WHERE {
                Graph ?g {
                ?ont a owl:Ontology
                }
            }"""
    return query
