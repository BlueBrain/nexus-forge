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
import collections
import datetime
from pathlib import Path
from typing import Dict, List, Union

import hjson
from rdflib import URIRef
from rdflib.namespace import XSD

from kgforge.core import Resource
from kgforge.core.archetypes import Model
from kgforge.core.commons.attributes import sort_attrs
from kgforge.core.commons.exceptions import ValidationError
from kgforge.core.commons.execution import not_supported, run
from kgforge.specializations.models.shacl.collectors import NodeProperties
from kgforge.specializations.models.shacl.materializer import ShapesMaterializer, as_term

DEFAULT_VALUE = {
    XSD.string: str(),
    XSD.normalizedString: str(),
    XSD.time: datetime.time().isoformat(),
    XSD.date: datetime.date(9999, 12, 31).isoformat(),
    XSD.dateTime: datetime.datetime(9999, 12, 31).isoformat(),
    XSD.boolean: bool(),
    XSD.decimal: int(),
    XSD.int: int(),
    XSD.integer: int(),
    XSD.positiveInteger: int(),
    XSD.negativeInteger: int(),
    XSD.nonPositiveInteger: int(),
    XSD.nonNegativeInteger: int(),
    XSD.long: int(),
    XSD.short: int(),
    XSD.unsignedLong: int(),
    XSD.unsignedInt: int(),
    XSD.unsignedShort: int(),
    XSD.byte: int(),
    XSD.unsignedByte: int(),
    XSD.float: float(),
    XSD.double: float(),
    XSD.base64Binary: int(),
    XSD.anyURI: str(),
}

DEFAULT_TYPE_ORDER = [str, float, int, bool, datetime.date, datetime.time]


class ShaclModel(Model):
    """Specialization of Model that follows SHACL shapes"""

    def __init__(self, source: str, **source_config) -> None:
        super().__init__(source, **source_config)

    # Vocabulary.

    def _prefixes(self) -> Dict[str, str]:
        return self.service.namespaces

    def _types(self) -> List[str]:
        return list(self.service.types_shapes_map.keys())

    # Templates.

    def template(self, type: str, only_required: bool, constraints: bool = False) -> str:
        if constraints is True:
            not_supported()
        schema = self._template(type, only_required)
        return hjson.dumps(schema, indent=4, item_sort_key=sort_attrs)

    def _template(self, type: str, only_required: bool) -> Dict:
        try:
            uri = self.service.types_shapes_map[type]
        except KeyError:
            raise ValueError("type not found")
        node_properties = self.service.materialize(uri)
        dictionary = parse_attributes(node_properties, only_required)
        return dictionary

    # Validation.

    def schema_id(self, type: str) -> str:
        try:
            return str(self.service.types_shapes_map[type])
        except KeyError:
            raise ValueError("type not found")

    def validate(self, data: Union[Resource, List[Resource]], execute_actions_before: bool) -> None:
        run(self._validate_one, self._validate_many, data, execute_actions=execute_actions_before,
            exception=ValidationError, monitored_status="_validated")

    def _validate_one(self, resource: Resource) -> None:
        not_supported()


    # Utils.

    @staticmethod
    def _service_from_directory(dirpath: Path) -> ShapesMaterializer:
        return ShapesMaterializer(dirpath)


def parse_attributes(node: NodeProperties, only_required: bool) -> Dict:
    attributes = dict()
    if hasattr(node, "id"):
        attributes["id"] = ""
    if hasattr(node, "path"):
        if only_required is True:
            if not hasattr(node, "mandatory"):
                return attributes
        if hasattr(node, "properties"):
            v = parse_properties(node.properties, only_required)
        else:
            v = parse_value(node)
        attributes[as_term(node.path)] = v
    elif hasattr(node, "properties"):
        attributes.update(parse_properties(node.properties, only_required))
    return attributes


def parse_properties(items: List[NodeProperties], only_required: bool) -> Dict:
    props = dict()
    for item in items:
        props.update(parse_attributes(item, only_required))
    return props


def parse_value(node):
    v = ""
    if hasattr(node, "values"):
        # node.constraint could be: in, or, xor
        if hasattr(node, "constraint"):
            if node.constraint == "in":
                v = sorted([default_value(val) for val in node.values])
            else:
                v = default_values(node.values)
        else:
            if not isinstance(node.values, list):
                v = default_value(node.values)
            else:
                if len(node.values) > 1:
                    v = default_values(node.values)
                else:
                    v = default_value(node.values[0])
    return v


def default_values(values):
    all_default_values = [data_value(val) for val in values]
    for data_type in DEFAULT_TYPE_ORDER:
        for val in all_default_values:
            if not isinstance(val, URIRef) and isinstance(val, data_type):
                return val
    if len(values) > 1:
        return [object_value(val) for val in sorted(values)]
    else:
        return as_term(values[0])


def default_value(value):
    if value in DEFAULT_VALUE:
        return DEFAULT_VALUE[value]
    elif isinstance(value, URIRef):
        return as_term(value)
    else:
        return value


def object_value(value):
    return {"type": as_term(value)}


def data_value(value):
    if value in DEFAULT_VALUE:
        return DEFAULT_VALUE[value]
    else:
        return value
