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
import datetime
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any

from rdflib import URIRef, Literal
from rdflib.namespace import XSD

from kgforge.core import Resource
from kgforge.core.archetypes import Model, Store
from kgforge.core.commons.context import Context
from kgforge.specializations.models.rdf.collectors import NodeProperties
from kgforge.specializations.models.rdf.directory_service import DirectoryService
from kgforge.specializations.models.rdf.service import RdfService
from kgforge.specializations.models.rdf.store_service import StoreService
from kgforge.specializations.models.rdf.utils import as_term

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


class RdfModel(Model):
    """Specialization of Model that follows SHACL shapes"""

    def __init__(self, source: str, **source_config) -> None:
        super().__init__(source, **source_config)

    # Vocabulary.

    def _prefixes(self) -> Dict[str, str]:
        return self.service.context.prefixes

    def _types(self) -> List[str]:
        return list(self.service.types_to_shapes.keys())

    def context(self) -> Context:
        return self.service.context

    def resolve_context(self, iri: str) -> Dict:
        return self.service.resolve_context(iri)

    def _generate_context(self) -> Context:
        document = self.service.generate_context()
        if document:
            return Context(document)

    # Templates.

    def _template(self, type: str, only_required: bool) -> Dict:
        try:
            uri = self.service.types_to_shapes[type]
        except KeyError:
            raise ValueError("type not found")
        node_properties = self.service.materialize(uri)
        dictionary = parse_attributes(node_properties, only_required)
        return dictionary

    # Validation.

    def schema_id(self, type: str) -> str:
        try:
            return str(self.service.types_to_shapes[type])
        except KeyError:
            raise ValueError("type not found")

    def _validate_one(self, resource: Resource) -> None:
        raise NotImplementedError("not implemented yet")

    # Utils.

    @staticmethod
    def _service_from_directory(dirpath: Path, context_iri: str, **dir_config) -> RdfService:
        return DirectoryService(dirpath, context_iri)

    @staticmethod
    def _service_from_store(store: Callable, context_config: Optional[Dict], **source_config) -> Any:
        endpoint = source_config.get("endpoint")
        token = source_config.get("token")
        bucket = source_config["bucket"]
        default_store: Store = store(endpoint, bucket, token)

        if context_config:
            context_endpoint = context_config.get("endpoint", default_store.endpoint)
            context_token = context_config.get("token", default_store.token)
            context_bucket = context_config.get("bucket", default_store.bucket)
            context_iri = context_config.get("iri")
            if (context_endpoint != default_store.endpoint
                    or context_token != default_store.token
                    or context_bucket != default_store.bucket):
                context_store: Store = store(context_endpoint, context_bucket, context_token)
                service = StoreService(default_store, context_iri, context_store)
            else:
                service = StoreService(default_store, context_iri, None)
        else:
            service = StoreService(default_store)

        return service


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
    elif isinstance(value, Literal):
        return value.toPython()
    else:
        return value


def object_value(value):
    return {"type": as_term(value)}


def data_value(value):
    if value in DEFAULT_VALUE:
        return DEFAULT_VALUE[value]
    else:
        return value
