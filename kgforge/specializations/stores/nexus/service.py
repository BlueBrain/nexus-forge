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

from typing import Callable, Dict, List, Optional, Union, Tuple, Type, Any
import asyncio
import copy
import json
from asyncio import Task
from copy import deepcopy
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse, parse_qs

import aiohttp
import nest_asyncio
import requests

from kgforge.core.resource import Resource

from kgforge.core.commons.constants import DEFAULT_REQUEST_TIMEOUT
from kgforge.core.commons.actions import (
    Action,
    collect_lazy_actions,
    execute_lazy_actions,
    LazyAction,
)

from kgforge.core.commons.exceptions import ConfigurationError, RunException
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import (
    _from_jsonld_one,
    _remove_ld_keys,
    as_jsonld,
    recursive_resolve,
)
import kgforge
from kgforge.core.wrappings.dict import wrap_dict
from kgforge.specializations.stores.nexus.http_helpers import views_fetch


from kgforge.core.conversions.rdf import _from_jsonld_one, _remove_ld_keys, recursive_resolve
from kgforge.core.wrappings.dict import wrap_dict


class Service:
    REQUEST_TIMEOUT = DEFAULT_REQUEST_TIMEOUT
    NEXUS_NAMESPACE_FALLBACK = "https://bluebrain.github.io/nexus/vocabulary/"
    NEXUS_CONTEXT_FALLBACK = "https://bluebrain.github.io/nexus/contexts/resource.json"
    NEXUS_CONTEXT_SOURCE_FALLBACK = (
        "https%3A%2F%2Fbluebrain.github.io%2Fnexus%2Fcontexts%2Fresource.json/source"
    )
    DEFAULT_SPARQL_INDEX_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}defaultSparqlIndex"
    DEFAULT_ES_INDEX_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}defaultElasticSearchIndex"
    DEPRECATED_PROPERTY_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}deprecated"
    PROJECT_PROPERTY_FALLBACK = f"{NEXUS_NAMESPACE_FALLBACK}project"
    UNCONSTRAINED_SCHEMA = "https://bluebrain.github.io/nexus/schemas/unconstrained.json"
    SHACL_SCHEMA = "https://bluebrain.github.io/nexus/schemas/shacl-20170720.ttl"

    SPARQL_ENDPOINT_TYPE = "sparql"
    ELASTIC_ENDPOINT_TYPE = "elastic"

    NEXUS_CONTENT_LENGTH_HEADER = "x-nxs-file-content-length"

    def __init__(
        self,
        endpoint: str,
        org: str,
        prj: str,
        token: str,
        model_context: Context,
        max_connection: int,
        searchendpoints: Dict,
        store_context: str,
        store_local_context: str,
        namespace: str,
        project_property: str,
        deprecated_property: bool,
        content_type: str,
        accept: str,
        files_upload_config: Dict,
        files_download_config: Dict,
        **params,
    ):
        self.endpoint = endpoint
        self.organisation = org
        self.project = prj
        self.model_context = model_context
        self.context_cache: Dict = {}
        self.max_connection = max_connection
        self.params = copy.deepcopy(params)
        self.store_context = store_context
        self.store_local_context = store_local_context
        self.namespace = namespace
        self.project_property = project_property
        self.store_metadata_keys = [
            "_constrainedBy",
            "_createdAt",
            "_createdBy",
            "_deprecated",
            "_incoming",
            "_outgoing",
            "_project",
            "_rev",
            "_schemaProject",
            "_self",
            "_updatedAt",
            "_updatedBy",
        ]

        self.deprecated_property = deprecated_property
        self.revision_property = f"{self.namespace}rev"
        self.default_sparql_index = f"{self.namespace}defaultSparqlIndex"
        self.default_es_index = f"{self.namespace}defaultElasticSearchIndex"

        self.headers = {"Content-Type": content_type, "Accept": accept}

        sparql_config = searchendpoints.get("sparql", None) if searchendpoints else None
        elastic_config = searchendpoints.get("elastic", None) if searchendpoints else None

        self.headers_sparql = {
            "Content-Type": (
                sparql_config["Content-Type"]
                if sparql_config and "Content-Type" in sparql_config
                else "text/plain"
            ),
            "Accept": (
                sparql_config["Accept"]
                if sparql_config and "Accept" in sparql_config
                else "application/sparql-results+json"
            ),
        }
        self.headers_elastic = {
            "Content-Type": (
                elastic_config["Content-Type"]
                if elastic_config and "Content-Type" in elastic_config
                else "application/json"
            ),
            "Accept": (
                elastic_config["Accept"]
                if elastic_config and "Accept" in elastic_config
                else "application/json"
            ),
        }
        self.headers_upload = {"Accept": files_upload_config.pop("Accept")}
        self.headers_download = {"Accept": files_download_config.pop("Accept")}

        self.token = token

        if token is not None:
            self.headers["Authorization"] = "Bearer " + token
            self.headers_sparql["Authorization"] = "Bearer " + token
            self.headers_elastic["Authorization"] = "Bearer " + token
            self.headers_upload["Authorization"] = "Bearer " + token
            self.headers_download["Authorization"] = "Bearer " + token

        self.context = Context(self.get_project_context())

        self.url_files = Service.make_endpoint(self.endpoint, "files", org, prj)
        self.url_resources = Service.make_endpoint(self.endpoint, "resources", org, prj)
        self.url_resolver = Service.make_endpoint(self.endpoint, "resolvers", org, prj)
        self.url_schemas = Service.make_endpoint(self.endpoint, "schemas", org, prj)

        self.metadata_context = Context(
            recursive_resolve(
                self.store_context, self.resolve_context, already_loaded=[]
            ),
            store_context,
        )
        sparql_view = (
            sparql_config["endpoint"]
            if sparql_config and "endpoint" in sparql_config
            else self.default_sparql_index
        )
        elastic_view = (
            elastic_config["endpoint"]
            if elastic_config and "endpoint" in elastic_config
            else self.default_es_index
        )
        default_str_keyword_field = (
            elastic_config["default_str_keyword_field"]
            if elastic_config and "default_str_keyword_field" in elastic_config
            else None
        )

        es_mapping = (
            elastic_config["mapping"]
            if elastic_config and "mapping" in elastic_config
            else None
        )

        self.sparql_endpoint = {
            "endpoint": self.make_query_endpoint_self(sparql_view, Service.SPARQL_ENDPOINT_TYPE)
        }

        self.elastic_endpoint = {
            "endpoint": self.make_query_endpoint_self(elastic_view, Service.ELASTIC_ENDPOINT_TYPE)
        }

        self.elastic_endpoint["view"] = LazyAction(
            views_fetch,
            self.endpoint,
            self.token,
            quote_plus(org),
            quote_plus(prj),
            es_mapping if es_mapping else elastic_view,  # Todo consider using Dict for es_mapping
        )
        self.elastic_endpoint["default_str_keyword_field"] = default_str_keyword_field

        # The following code is for async to work on jupyter notebooks
        try:
            asyncio.get_event_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

    @staticmetho
    def make_endpoint(endpoint: str, endpoint_type: str, organisation: str, project: str):
        return "/".join(
            (endpoint, endpoint_type, quote_plus(organisation), quote_plus(project))
        )

    @staticmethod
    def add_resource_id_to_endpoint(
            endpoint: str, resource_id: Optional[str]
    ):
        if resource_id:
            return "/".join([endpoint, quote_plus(resource_id)])
        else:
            return endpoint

    @staticmethod
    def add_schema_and_id_to_endpoint(
            endpoint: str, schema_id: Optional[str], resource_id: Optional[str]
    ):
        schema = quote_plus(schema_id) if schema_id else "_"

        to_join = [endpoint, schema]

        if resource_id:
            to_join.append(quote_plus(resource_id))

        return "/".join(to_join)

    @staticmethod
    def _format_version(version: Any, error_to_throw: Type[RunException]) -> Optional[Dict]:
        if version is not None:
            if isinstance(version, int):
                version_params = {"rev": version}
            elif isinstance(version, str):
                version_params = {"tag": version}
            else:
                raise error_to_throw("incorrect 'version'")
        else:
            version_params = None

        return version_params

    @staticmethod
    def make_query_endpoint(endpoint, view, endpoint_type, organisation, project) -> str:

        if endpoint_type == Service.SPARQL_ENDPOINT_TYPE:
            last_url_component = "sparql"
        elif endpoint_type == Service.ELASTIC_ENDPOINT_TYPE:
            last_url_component = "_search"
        else:
            raise ValueError(f"Unknown endpoint type {endpoint_type}")

        view_base = Service.make_endpoint(endpoint, "views", organisation, project)

        return "/".join((view_base, quote_plus(view), last_url_component))

    def make_query_endpoint_self(self, view: str, endpoint_type: str):
        return Service.make_query_endpoint(
            endpoint=self.endpoint, view=view,
            endpoint_type=endpoint_type,
            organisation=self.organisation,
            project=self.project
        )

    def get_project_context(self) -> Dict:
        project_data = kgforge.specializations.stores.nexus.http_helpers.project_fetch(endpoint=self.endpoint, token=self.token, org_label=self.organisation, project_label=self.project)
        context = {"@base": project_data["base"], "@vocab": project_data["vocab"]}
        for mapping in project_data["apiMappings"]:
            context[mapping["prefix"]] = mapping["namespace"]
        return context

    def resolve_context(self, iri: str, local_only: Optional[bool] = False) -> Dict:
        if iri in self.context_cache:
            return self.context_cache[iri]
        try:
            context_to_resolve = (
                self.store_local_context if iri == self.store_context else iri
            )

            url = Service.add_schema_and_id_to_endpoint(
                endpoint=self.url_resolver,
                schema_id=None
                resource_id=context_to_resolve
            )

            response = requests.get(url, headers=self.headers, timeout=Service.REQUEST_TIMEOUT)
            response.raise_for_status()
            resource = response.json()
        except Exception as exc:
            if not local_only:
                try:
                    context = Context(context_to_resolve)
                except URLError as exc2:
                    raise ValueError(
                        f"{context_to_resolve} is not resolvable"
                    ) from exc2

                document = context.document["@context"]
            else:
                raise ValueError(f"{context_to_resolve} is not resolvable") from exc
        else:
            # Make sure context is not deprecated
            if "_deprecated" in resource and resource["_deprecated"]:
                raise ConfigurationError(
                    f"Context {context_to_resolve} exists but was deprecated"
                )
            document = json.loads(json.dumps(resource["@context"]))
        if isinstance(document, list):
            if self.store_context in document:
                document.remove(self.store_context)
            if self.store_local_context in document:
                document.remove(self.store_local_context)
        self.context_cache.update({context_to_resolve: document})
        return document

    @staticmethod
    def _local_parse(id_value, version_params) -> Tuple[str, Dict]:
        parsed_id = urlparse(id_value)
        fragment = None
        query_params = {}

        # urlparse is not separating fragment and query params when the latter are put after a fragment
        if parsed_id.fragment is not None and "?" in str(parsed_id.fragment):
            fragment_parts = urlparse(parsed_id.fragment)
            query_params = parse_qs(fragment_parts.query)
            fragment = fragment_parts.path
        elif parsed_id.fragment is not None and parsed_id.fragment != "":
            fragment = parsed_id.fragment
        elif parsed_id.query is not None and parsed_id.query != "":
            query_params = parse_qs(parsed_id.query)

        if version_params is not None:
            query_params.update(version_params)

        formatted_fragment = '#' + fragment if fragment is not None else ''
        id_without_query = f"{parsed_id.scheme}://{parsed_id.netloc}{parsed_id.path}{formatted_fragment}"

        return id_without_query, query_params

    def sync_metadata(self, resource: Resource, result: Dict) -> None:
        metadata = (
            {"id": resource.id}
            if hasattr(resource, "id")
            else (
                {"id": resource.__getattribute__("@id")}
                if hasattr(resource, "@id")
                else {}
            )
        )
        keys = sorted(self.metadata_context.terms.keys())
        keys.extend(["_index", "_score", "id", "@id"])
        only_meta = {k: v for k, v in result.items() if k in keys}
        metadata.update(_remove_ld_keys(only_meta, self.metadata_context, False))
        if not hasattr(resource, "id") and not hasattr(resource, "@id"):
            resource.id = result.get("id", result.get("@id", None))
        resource._store_metadata = wrap_dict(metadata)

    def synchronize_resource(
            self,
            resource: Resource,
            response: Optional[Union[Exception, Dict]],
            action_name: str,
            succeeded: bool,
            synchronized: bool,
    ) -> None:
        if succeeded:
            action = Action(action_name, succeeded, None)
            if response:  # for requests that don't return metadata on success
                self.sync_metadata(resource, response)
        else:
            action = Action(action_name, succeeded, response)

        resource._last_action = action
        resource._synchronized = synchronized

    def default_callback(self, fun_name: str) -> Callable:
        def callback(task: Task):
            result = task.result()

            succeeded = not isinstance(result.response, Exception)

            self.synchronize_resource(
                resource=result.resource, response=result.response, action_name=fun_name,
                succeeded=succeeded, synchronized=succeeded
            )

        return callback

    def verify(
        self,
        resources: List[Resource],
        function_name,
        exception: Type[Exception],
        id_required: bool,
        required_synchronized: bool,
        execute_actions: bool,
    ) -> List[Resource]:
        valid = []
        for resource in resources:
            if id_required and not hasattr(resource, "id"):
                error = exception("resource should have an id")
                self.synchronize_resource(resource, error, function_name, False, False)
                continue
            if required_synchronized is not None:
                synchronized = resource._synchronized
                if synchronized is not required_synchronized:
                    be_or_not_be = "be" if required_synchronized is True else "not be"
                    error = exception(f"resource should {be_or_not_be} synchronized")
                    self.synchronize_resource(
                        resource, error, function_name, False, False
                    )
                    continue
            if execute_actions:
                lazy_actions = collect_lazy_actions(resource)
                if lazy_actions is not None:
                    try:
                        execute_lazy_actions(resource, lazy_actions)
                    except Exception as e:
                        self.synchronize_resource(
                            resource, exception(e), function_name, False, False
                        )
                        continue
            valid.append(resource)
        return valid

    def to_resource(
        self, payload: Dict, sync_metadata: bool = True, **kwargs
    ) -> Resource:
        # Use JSONLD context defined in Model if no context is retrieved from payload
        # Todo: BlueBrainNexus store is not indexing in ES the JSONLD context, user provided context can be changed to Model defined one
        data_context = deepcopy(
            payload.get(
                "@context", self.model_context.iri if self.model_context else None
            )
        )
        if not isinstance(data_context, list):
            data_context = [data_context]
        if self.store_context in data_context:
            data_context.remove(self.store_context)
        if self.store_local_context in data_context:
            data_context.remove(self.store_local_context)
        data_context = data_context[0] if len(data_context) == 1 else data_context
        metadata = {}
        data = {}
        for k, v in payload.items():
            if k in self.metadata_context.terms.keys():
                metadata[k] = v
            else:
                data[k] = v

        if (
            self.model_context
            and data_context is not None
            and data_context == self.model_context.iri
        ):
            resolved_ctx = self.model_context.document["@context"]
        elif data_context is not None:
            resolved_ctx = recursive_resolve(
                data_context,
                self.resolve_context,
                already_loaded=[self.store_local_context, self.store_context],
            )
        else:
            resolved_ctx = None
        if resolved_ctx:
            data["@context"] = resolved_ctx
            resource = _from_jsonld_one(data)
            resource.context = data_context
        else:
            resource = Resource.from_json(data)

        if len(metadata) > 0 and sync_metadata:
            metadata.update(kwargs)
            self.sync_metadata(resource, metadata)
        if not hasattr(resource, "id") and kwargs and "id" in kwargs.keys():
            resource.id = kwargs.get("id")
        return resource


def _error_message(error: Union[requests.HTTPError, aiohttp.ClientResponseError, Dict]) -> str:
    def format_message(msg: str):
        return "".join(
            [msg[0].lower(), msg[1:-1], msg[-1] if msg[-1] != "." else ""]
        )

    try:
        error_json = error.response.json() if \
            isinstance(error, (requests.HTTPError, aiohttp.ClientResponseError)) \
            else error

        messages = []
        reason = error_json.get("reason", None)
        details = error_json.get("details", None)

        if reason and isinstance(reason, str):
            messages.append(format_message(reason))
        if details and isinstance(details, str):
            messages.append(format_message(details))

        messages = messages if len(messages) > 0 else [str(error)]
        return ". ".join(messages)
    except Exception:
        pass

    try:
        error_text = error.response.text() if isinstance(error, requests.HTTPError) else str(error)
        return format_message(error_text)
    except Exception:
        return format_message(str(error))
