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
import datetime
import re
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any, Union

from pyshacl.consts import SH
from rdflib import URIRef, Literal
from rdflib.namespace import XSD

from kgforge.core.archetypes.mapping import Mapping
from kgforge.core.resource import Resource
from kgforge.core.archetypes.store import Store
from kgforge.core.archetypes.model import Model
from kgforge.core.commons.actions import Action
from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import ValidationError
from kgforge.core.commons.execution import run, not_supported
from kgforge.specializations.models.rdf.collectors import NodeProperties
from kgforge.specializations.models.rdf.directory_service import DirectoryService
from kgforge.specializations.models.rdf.service import RdfService
from kgforge.specializations.models.rdf.store_service import StoreService
from kgforge.specializations.models.rdf.utils import as_term

DEFAULT_VALUE = {
    XSD.string: str(),
    XSD.normalizedString: str(),
    XSD.anyURI: str(),
    XSD.float: float(),
    XSD.double: float(),
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
    XSD.base64Binary: int(),
    XSD.boolean: bool(),
    XSD.time: datetime.time().isoformat(),
    XSD.date: datetime.date(9999, 12, 31).isoformat(),
    XSD.dateTime: datetime.datetime(9999, 12, 31).isoformat(),
}

DEFAULT_TYPE_ORDER = [str, float, int, bool, datetime.date, datetime.time]


class RdfModel(Model):
    """Specialization of Model that follows SHACL shapes"""

    # Vocabulary.

    def _prefixes(self) -> Dict[str, str]:
        return self.service.context.prefixes

    def _types(self) -> List[str]:
        return [
            self.service.context.to_symbol(str(cls))
            for cls in self.service.class_to_shape.keys()
        ]

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
            shape_iri = self.service.get_shape_uriref_from_class_fragment(type)
            node_properties = self.service.materialize(shape_iri)
            dictionary = parse_attributes(node_properties, only_required, None)
            return dictionary
        except Exception as exc:
            raise ValueError(f"Unable to generate template:{str(exc)}") from exc

    # Validation.

    def schema_id(self, type: str) -> str:
        try:
            shape_iri = self.service.get_shape_uriref_from_class_fragment(type)
            return self.service.schema_id(shape_iri)
        except Exception as exc:
            raise ValueError(f"Unable to get the schema id:{str(exc)}") from exc

    def validate(
        self,
        data: Union[Resource, List[Resource]],
        execute_actions_before: bool,
        type_: str,
        inference: str = None,
    ) -> None:
        run(
            self._validate_one,
            self._validate_many,
            data,
            execute_actions=execute_actions_before,
            exception=ValidationError,
            monitored_status="_validated",
            type_=type_,
            inference=inference,
        )

    def _validate_many(
        self, resources: List[Resource], type_: str, inference: str
    ) -> None:
        for resource in resources:
            conforms, graph, _ = self.service.validate(
                resource, type_=type_, inference=inference
            )
            if conforms:
                resource._validated = True
                action = Action(self._validate_many.__name__, conforms, None)
            else:
                resource._validated = False
                violations = set(
                    " ".join(re.findall("[A-Z][^A-Z]*", as_term(o)))
                    for o in graph.objects(None, SH.sourceConstraintComponent)
                )
                message = f"violation(s) of type(s) {', '.join(sorted(violations))}"
                action = Action(
                    self._validate_many.__name__, conforms, ValidationError(message)
                )

            resource._last_action = action

    def _validate_one(self, resource: Resource, type_: str, inference: str) -> None:
        conforms, _, report = self.service.validate(resource, type_, inference)
        if conforms is False:
            raise ValidationError("\n" + report)

    # Utils.

    @staticmethod
    def _service_from_directory(
        dirpath: Path, context_iri: str, **dir_config
    ) -> RdfService:
        return DirectoryService(dirpath, context_iri)

    @staticmethod
    def _service_from_store(
        store: Callable, context_config: Optional[Dict], **source_config
    ) -> Any:

        default_store: Store = store(**source_config)

        if context_config:
            context_endpoint = context_config.get("endpoint", default_store.endpoint)
            context_token = context_config.get("token", default_store.token)
            context_bucket = context_config.get("bucket", default_store.bucket)
            context_iri = context_config.get("iri")
            if (
                context_endpoint != default_store.endpoint
                or context_token != default_store.token
                or context_bucket != default_store.bucket
            ):
                source_config.pop("endpoint", None)
                source_config.pop("token", None)
                source_config.pop("bucket", None)
                context_store: Store = store(
                    endpoint=context_endpoint,
                    bucket=context_bucket,
                    token=context_token,
                    **source_config,
                )
                # FIXME: define a store independent StoreService
                service = StoreService(default_store, context_iri, context_store)
            else:
                service = StoreService(default_store, context_iri, None)
        else:
            service = StoreService(default_store)

        return service

    def _sources(self) -> List[str]:
        raise not_supported()

    def _mappings(self, source: str) -> Dict[str, List[str]]:
        raise not_supported()

    def mapping(self, entity: str, source: str, type: Callable) -> Mapping:
        raise not_supported()

    @staticmethod
    def _service_from_url(url: str, context_iri: Optional[str]) -> Any:
        raise not_supported()


def parse_attributes(
    node: NodeProperties, only_required: bool, inherited_constraint: Optional[str]
) -> Dict:
    attributes = {}
    if hasattr(node, "path"):
        if only_required is True:
            if not hasattr(node, "mandatory"):
                return attributes
        if hasattr(node, "properties"):
            parent_constraint = node.constraint if hasattr(node, "constraint") else None
            v = parse_properties(node.properties, only_required, parent_constraint)
        else:
            v = parse_value(node, inherited_constraint)
        attributes[as_term(node.path)] = v
    elif hasattr(node, "properties"):
        parent_constraint = node.constraint if hasattr(node, "constraint") else None
        attributes.update(
            parse_properties(node.properties, only_required, parent_constraint)
        )
    return attributes


def parse_properties(
    items: List[NodeProperties], only_required: bool, inherited_constraint: str
) -> Dict:
    props = {}
    for item in items:
        props.update(parse_attributes(item, only_required, inherited_constraint))
    return props


def parse_value(node: NodeProperties, parent_constraint: str) -> Any:
    v = ""
    if hasattr(node, "values"):
        # node.constraint could be: in, or, xor
        if hasattr(node, "constraint") or parent_constraint:
            constraint = parent_constraint or node.constraint
            if constraint in ("in", "or", "xone"):
                v = default_values(node.values, one=False)
            else:
                v = default_values(node.values, one=True)
        else:
            v = default_values(node.values, one=True)
    return v


def default_values(values, one: bool):
    if isinstance(values, list):
        all_default_values = [default_value(v) for v in values]
        if all_default_values:
            if one:
                for data_type in DEFAULT_TYPE_ORDER:
                    for val in all_default_values:
                        if isinstance(val, data_type):
                            return val
            else:
                first_type = type(all_default_values[0])
                sortable = all(isinstance(v, first_type) for v in all_default_values)
                if sortable:
                    return sorted(all_default_values)

                types_position = {
                    DEFAULT_TYPE_ORDER.index(type(v)): v for v in all_default_values
                }
                return [types_position[k] for k in sorted(types_position.keys())]
    else:
        return default_value(values)


def default_value(value):
    # TODO: replace the as_term function with context.to_symbol
    if value in DEFAULT_VALUE:
        return DEFAULT_VALUE[value]
    if isinstance(value, URIRef):
        return as_term(value)
    if isinstance(value, Literal):
        return value.toPython()

    return value


def object_value(value):
    return {"type": as_term(value)}


def data_value(value):
    if value in DEFAULT_VALUE:
        return DEFAULT_VALUE[value]

    return value
