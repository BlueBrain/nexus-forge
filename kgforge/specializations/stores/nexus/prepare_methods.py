import copy
from typing import Dict, Optional, Tuple, Type
from typing_extensions import TypeAlias
from aiohttp import hdrs

from kgforge.core.resource import Resource
import kgforge.core.commons.exceptions as run_exceptions
from kgforge.core.conversions.rdf import as_jsonld
from kgforge.specializations.stores.nexus.service import Service

prepare_return: TypeAlias = Tuple[
    str, str, Resource, Type[run_exceptions.RunException], Dict, Optional[Dict], Optional[Dict]
    # method, url, resource, exception to throw, headers, params, payload
]

# TODO maybe params as a separate arg is not necessary.
#  Used to be only service parameters being propagated,
#  but since the service is available, the param can be retrieved here


def _make_url(service: Service,
              schema_id: str,
              identifier: str):
    if schema_id == service.SHACL_SCHEMA:
        url = Service.add_resource_id_to_endpoint(
            service.url_schemas, resource_id=identifier
        )
    else:
        url = Service.add_schema_and_id_to_endpoint(
            service.url_resources, schema_id=schema_id, resource_id=identifier
        )
    return url


def prepare_create(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    schema_id = kwargs.get("schema_id")

    params_register = copy.deepcopy(service.params.get("register", {}))

    identifier = resource.get_identifier()

    url = _make_url(service, schema_id, identifier)

    context = service.model_context or service.context

    payload = as_jsonld(
        resource,
        "compacted",
        False,
        model_context=context,
        metadata_context=None,
        context_resolver=service.resolve_context
    )

    method = hdrs.METH_PUT if identifier else hdrs.METH_POST
    exception = run_exceptions.RegistrationError

    return method, url, resource, exception, service.headers, params_register, payload


def prepare_update(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    schema_id = kwargs.get("schema_id")
    url, params = _prepare_uri(service, resource, schema_id, keep_unconstrained=True)
    params_update = copy.deepcopy(service.params.get("update", {}))
    params_update.update(params)

    payload = as_jsonld(
        resource,
        "compacted",
        False,
        model_context=service.model_context or service.context,
        metadata_context=None,
        context_resolver=service.resolve_context
    )

    method = hdrs.METH_PUT
    exception = run_exceptions.UpdatingError

    return method, url, resource, exception, service.headers, params_update, payload


def _prepare_uri(
        service, resource: Resource, schema_uri: Optional[str] = None,
        keep_unconstrained: bool = False
) -> Tuple[str, Dict]:
    schema_id = schema_uri or resource._store_metadata._constrainedBy


    if schema_id == service.UNCONSTRAINED_SCHEMA and not keep_unconstrained:
        schema_id = None

    url = _make_url(service, schema_id, resource.id)
    url = Service.add_schema_and_id_to_endpoint(
        service.url_resources, schema_id, resource_id=resource.id
    )

    rev = resource._store_metadata._rev
    params = {"rev": rev}
    return url, params


def _prepare_tag(service: Service, resource: Resource, tag: str) -> Tuple[str, Dict, Dict]:
    url, params = _prepare_uri(service, resource)
    url = f"{url}/tags"
    data = {"tag": tag}
    data.update(params)
    return url, data, params


def prepare_tag(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    provided_tag = kwargs.get("tag")

    url, payload, rev_param = _prepare_tag(service, resource, provided_tag)

    params_tag = copy.deepcopy(service.params.get("tag", {}))
    params_tag.update(rev_param)

    method = hdrs.METH_POST
    exception = run_exceptions.TaggingError

    return method, url, resource, exception, service.headers, params_tag, payload


def prepare_deprecate(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    params_deprecate = copy.deepcopy(service.params.get("deprecate", {}))
    url, rev_param = _prepare_uri(service, resource)
    params_deprecate.update(rev_param)

    method = hdrs.METH_DELETE
    exception = run_exceptions.DeprecationError
    payload = None

    return method, url, resource, exception, service.headers, params_deprecate, payload


def prepare_fetch(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    resource_org, resource_prj = resource._project.split("/")[-2:]
    endpoint = Service.make_endpoint(service.endpoint, "resources", resource_org, resource_prj)
    url = Service.add_schema_and_id_to_endpoint(
        endpoint=endpoint, schema_id=None, resource_id=resource.id
    )

    fetch_params = copy.deepcopy(service.params.get("retrieve", {}))

    if hasattr(resource, "_rev"):
        fetch_params["rev"] = resource._rev

    retrieve_source = kwargs.pop("retrieve_source", False)

    if retrieve_source:
        url = "/".join((url, "source"))

    method = hdrs.METH_GET
    exception = run_exceptions.QueryingError
    payload = None

    return method, url, resource, exception, service.headers, fetch_params, payload


def prepare_update_schema(
        service: Service,
        resource: Resource,
        **kwargs
) -> prepare_return:

    schema_id = kwargs.get("schema_id")
    url = Service.add_schema_and_id_to_endpoint(
        endpoint=service.url_resources, schema_id=schema_id, resource_id=resource.id
    )

    method = hdrs.METH_PUT
    url = f"{url}/update-schema"
    exception = run_exceptions.SchemaUpdateError
    payload = None
    update_schema_params = None

    return method, url, resource, exception, service.headers, update_schema_params, payload
