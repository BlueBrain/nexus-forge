import re
from typing import Optional, Union, Dict, Callable

import nexussdk as nexus

from kgforge.core import Resource, Resources
from kgforge.core.commons.actions import run
from kgforge.core.commons.attributes import not_supported
from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, dispatch
from kgforge.core.commons.wrappers import DictWrapper
from kgforge.core.storing.exceptions import RegistrationError, DeprecationError, RetrievalError, TaggingError
from kgforge.core.storing.store import Store
from kgforge.core.transforming.converters import Converters


class BlueBrainNexus(Store):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        try:
            self.organisation, self.project = self.bucket.split('/')
        except ValueError:
            raise ValueError("malformed bucket parameter, expecting 'organization/project' like")
        else:
            nexus.config.set_environment(self.endpoint)
            nexus.config.set_token(self.token)

    def _register_many(self, resources: Resources, update: bool) -> None:
        run(self._register, resources, status="_synchronized", update=update)

    def _register_one(self, resource: Resource, update: bool) -> None:
        run(self._register, resource, status="_synchronized", update=update)

    def _register(self, resource: Resource, update: bool) -> None:
        if update and not hasattr(resource, "id"):
            raise RegistrationError(f"Can't update a resource that does not have an id")
        data = Converters.as_jsonld(resource, True, True)
        if update:
            if resource._synchronized:
                raise RegistrationError(f"Resource is synchronized, update has no effect")
            try:
                response = nexus.resources.update(data)
            except nexus.HTTPError as e:
                self._raise_nexus_http_error(e, RegistrationError)
            else:
                self._sync_metadata(resource, response)
        else:
            try:
                response = nexus.resources.create(org_label=self.organisation, project_label=self.project, data=data)
            except nexus.HTTPError as e:
                self._raise_nexus_http_error(e, RegistrationError)
            else:
                resource.id = response['@id']
                # If resource had no context, update it with the one provided by the store.
                if not hasattr(resource, '_context'):
                    remote = self.retrieve(resource.id)
                    resource._context = remote._context
                self._sync_metadata(resource, response)

    # C[R]UD

    @catch
    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        try:
            if isinstance(version, int):
                response = nexus.resources.fetch(org_label=self.organisation, project_label=self.project,
                                                 resource_id=id, rev=version)
            else:
                response = nexus.resources.fetch(org_label=self.organisation, project_label=self.project,
                                                 resource_id=id, tag=version)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, RetrievalError)
        else:
            resource = self._to_resource(response)
            resource._synchronized = True
            self._sync_metadata(resource, response)
            return resource

    # CR[U]D

    @catch
    def tag(self, data: ManagedData, value: str) -> None:
        dispatch(data, self._tag_many, self._tag_one, value)

    def _tag_many(self, resources: Resources, value: str) -> None:
        run(self._tag, resources, status="_synchronized", tag=value)

    def _tag_one(self, resource: Resource, value: str) -> None:
        run(self._tag, resource, status="_synchronized", tag=value)

    def _tag(self, resource: Resource, value: str) -> None:
        if resource._synchronized is False:
            raise TaggingError("The resource has changes that have not being registered")
        if resource._last_action.operation == "_tag" and resource._last_action.succeeded:
            raise TaggingError(f"The current version of the resource has being already tagged")
        try:
            payload = Converters.as_jsonld(resource, True, True)
            response = nexus.resources.tag(payload, value)
            self._sync_metadata(resource, response)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, TaggingError)

    # CRU[D]

    @catch
    def deprecate(self, data: ManagedData) -> None:
        dispatch(data, self._deprecate_many, self._deprecate_one)

    def _deprecate_many(self, resources: Resources):
        run(self._deprecate, resources, status="_synchronized")

    def _deprecate_one(self, resource: Resource):
        run(self._deprecate, resource, status="_synchronized")

    def _deprecate(self, resource: Resource):
        try:
            payload = Converters.as_jsonld(resource, True, True)
            response = nexus.resources.deprecate(payload)
            self._sync_metadata(resource, response)
        except nexus.HTTPError as e:
            self._raise_nexus_http_error(e, DeprecationError)

    # Query

    @catch
    def search(self, resolvers: "OntologiesHandler", *filters, **params) -> Resources:
        not_supported()

    @classmethod
    def _to_resource(cls, data: Dict) -> Resource:
        # FIXME: ideally a rdf-native solution

        def create_resource(dictionary: dict, ctx_base: str) -> Resource:
            rec = Resource()
            if "@id" in dictionary:
                rec.id = f"{ctx_base}{dictionary.pop('@id')}" if ctx_base else dictionary.pop("@id")
            if "@type" in dictionary:
                rec.type = dictionary.pop("@type")
            for k, v in dictionary.items():
                if not re.match(r"^_|@", k):
                    # TODO: use nexus namespace to properly identify metadata
                    if isinstance(v, dict):
                        setattr(rec, k, create_resource(v, ctx_base))
                    elif isinstance(v, list):
                        setattr(rec, k,
                                [create_resource(item, ctx_base) if isinstance(item, dict) else item for item in v])
                    else:
                        setattr(rec, k, v)
            return rec

        context = data.pop("@context", None)
        base = Converters.find_in_context(context, "@base") if context is not None else None
        resource = create_resource(data, base)
        if context is not None:
            resource._context = context
        return resource

    @staticmethod
    def _sync_metadata(resource: Resource, result: Dict) -> None:
        # TODO: use nexus namespace to properly identify its metadata
        metadata = {k: v for k, v in result.items() if k.startswith("_")}
        resource._store_metadata = DictWrapper._wrap(metadata)

    @staticmethod
    def _raise_nexus_http_error(error: nexus.HTTPError, error_type: Callable):
        try:
            reason = error.response.json()["reason"]
        except IndexError:
            reason = error.response.text()
        finally:
            raise error_type(reason)
