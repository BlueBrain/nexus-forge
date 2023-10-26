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
from typing import Tuple, List, Dict, Optional, Any
from kgforge.core.conversions.rdf import from_jsonld
from kgforge.core.resource import Resource
import rdflib
from rdflib.plugins.sparql.parser import Query

from kgforge.core.archetypes.resolver import Resolver
from kgforge.core.commons.context import Context
from kgforge.core.commons.files import is_valid_url
from kgforge.core.commons.parser import _parse_type
from kgforge.core.commons.query_builder import QueryBuilder

from pyld import jsonld


class CategoryDataType(Enum):
    DATETIME = "datetime"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LITERAL = "literal"


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
    CategoryDataType.BOOLEAN: lambda x: "'true'^^xsd:boolean" if x is True else "'false'^^xsd:boolean",
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
        schema: Dict,
        resolvers: Optional[List[Resolver]],
        context: Context,
        *filters,
        **params,
    ) -> Tuple[List, List]:

        statements = list()
        sparql_filters = list()
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
                        statements.append(f"{property_path} {_box_value_as_full_iri(f.value)}")
                    elif f.operator == "__ne__":
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(f"FILTER(?v{index} != {f.value})")
                    else:
                        raise NotImplementedError(
                            f"supported operators are '==' and '!=' when filtering by type or id."
                        )
                else:
                    parsed_type, parsed_value = _parse_type(f.value, parse_str=False)
                    value_type = type_map[parsed_type]
                    value = format_type[value_type](parsed_value if parsed_value else f.value)
                    if value_type is CategoryDataType.LITERAL:
                        if f.operator not in ["__eq__", "__ne__"]:
                            raise NotImplementedError(f"supported operators are '==' and '!=' when filtering with a str.")
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(f"FILTER(?v{index} = {_box_value_as_full_iri(value)})")
                    else:
                        statements.append(f"{property_path} ?v{index}")
                        sparql_filters.append(
                            f"FILTER(?v{index} {sparql_operator_map[f.operator]} {_box_value_as_full_iri(value)})"
                        )
            except NotImplementedError as nie:
                raise ValueError(f"Operator '{sparql_operator_map[f.operator]}' is not supported with the value '{f.value}': {str(nie)}")
        return statements, sparql_filters

    @staticmethod
    def build_resource_from_response(query: str, response: Dict, context: Context) -> List[Resource]:
        _, q_comp = Query.parseString(query)
        if q_comp.name == "ConstructQuery":
            subject_triples = {}
            for r in response["results"]["bindings"]:
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
                graph = rdflib.Graph().parse(data=triples, format="nt")
                data_expanded = json.loads(graph.serialize(format="json-ld"))
                data_expanded = json.loads(graph.serialize(format="json-ld"))
                frame = {"@id": iri}
                data_framed = jsonld.frame(data_expanded, frame)
                compacted = jsonld.compact(data_framed, context.document)
                resource = from_jsonld(compacted)
                resource.context = (
                    context.iri
                    if context.is_http_iri()
                    else context.document["@context"]
                )
                return resource

            return [triples_to_resource(s, t) for s, t in subject_triples.items()]
        else:
            # SELECT QUERY
            results = response["results"]["bindings"]
            return [
                Resource(**{k: json.loads(str(v["value"]).lower()) if v['type'] == 'literal' and
                            ('datatype' in v and v['datatype'] ==
                                'http://www.w3.org/2001/XMLSchema#boolean')
                            else (int(v["value"]) if v['type'] == 'literal' and
                                    ('datatype' in v and v['datatype'] ==
                                    'http://www.w3.org/2001/XMLSchema#integer')
                                    else v["value"]
                                    )
                            for k, v in x.items()})
                for x in results
            ]


def _box_value_as_full_iri(value):
    return f"<{value}>" if is_valid_url(value) else value
