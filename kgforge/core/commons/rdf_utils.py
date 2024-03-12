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
from typing import List
from rdflib import Graph
from rdflib.util import guess_format
from pathlib import Path
from kgforge.core.commons.context import Context

from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder


def build_shacl_query(
    statements: List[str] = None,
    defining_property_uri: str = None,
    deprecated_property_uri: str = None,
    optional: bool = False,
    search_in_graph: bool = False,
    context: Context = None,
) -> str:
    deprecated_statement = (
        f"?resource_id <{deprecated_property_uri}> ?_deprecated"
        if deprecated_property_uri
        else ""
    )
    defining_statement = (
        f"?resource_id <{defining_property_uri}> ?shape"
        if defining_property_uri
        else ""
    )
    if optional and deprecated_property_uri:
        deprecated_statement = " OPTIONAL {" + deprecated_statement + "}"
    if optional and defining_property_uri:
        defining_statement = " OPTIONAL {" + defining_statement + "}"

    shape_target_statements = "?shape sh:targetClass ?type"
    shape_node_statements = "SELECT (?shape as ?type) ?shape ?resource_id WHERE { ?shape a sh:NodeShape . ?shape a rdfs:Class"
    extra_statements = [defining_statement] + [deprecated_statement]
    if statements:
        extra_statements.extend(statements)
    shape_target_statements_str = ".".join([shape_target_statements] + extra_statements)
    shape_node_statements_str = (
        ".".join([shape_node_statements] + extra_statements) + "}"
    )
    all_statements = [shape_target_statements_str, shape_node_statements_str]
    vars_ = ["?type", "?shape", "?resource_id"]
    if search_in_graph:
        vars_.append("?g")
    shacl_query = SPARQLQueryBuilder._create_select_query(
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
