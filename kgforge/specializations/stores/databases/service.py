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

import asyncio
import copy
from difflib import context_diff
import json
import re
from pathlib import Path
from asyncio import Task
from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Callable, Dict, List, Optional, Union, Tuple
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse

import nest_asyncio
import nexussdk as nexus
import requests
from aiohttp import ClientSession, hdrs
from numpy import nan
from requests import HTTPError

from kgforge.core import Resource
from kgforge.core.commons.actions import (
    Action,
    collect_lazy_actions,
    execute_lazy_actions,
    LazyAction,
)
from kgforge.core.commons.context import Context
from kgforge.core.conversions.rdf import (
    _from_jsonld_one,
    _remove_ld_keys,
    as_jsonld,
    recursive_resolve,
)
from kgforge.core.wrappings.dict import wrap_dict


class Service:

    def __init__(
        self,
        endpoint: str,
        model_context: Context,
        max_connection: int,
        searchendpoints: Dict,
        content_type: str,
        accept: str,
        **params,
    ):

        self.endpoint = endpoint
        self.model_context = model_context
        self.context_cache: Dict = dict()
        self.max_connection = max_connection
        self.params = copy.deepcopy(params)

        self.headers = {"Content-Type": content_type, "Accept": accept}

        sparql_config = (
            searchendpoints["sparql"]
            if searchendpoints and "sparql" in searchendpoints
            else None
        )

        self.headers_sparql = {
            "Content-Type": sparql_config["Content-Type"]
            if sparql_config and "Content-Type" in sparql_config
            else "text/plain",
            "Accept": sparql_config["Accept"]
            if sparql_config and "Accept" in sparql_config
            else "application/sparql-results+json",
        }

        self.sparql_endpoint = dict()
        self.sparql_endpoint["endpoint"] = searchendpoints["sparql"]["endpoint"]
        self.sparql_endpoint["type"] = "sparql"

        # The following code is for async to work on jupyter notebooks
        try:
            asyncio.get_event_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

    def resolve_context(self, iri: str) -> Dict:
        if iri in self.context_cache:
            return self.context_cache[iri]
        context_to_resolve = iri
        try:
            context = Context(context_to_resolve)
        except URLError:
            raise ValueError(f"{context_to_resolve} is not resolvable")
        else:
            document = context.document["@context"]
        self.context_cache.update({context_to_resolve: document})
        return document

    def to_resource(
        self, payload: Dict, sync_metadata: bool = True, **kwargs
    ) -> Resource:
        # Use JSONLD context defined in Model if no context is retrieved from payload
        # Todo: BlueBrainNexus store is not indexing in ES the JSONLD context, user provided context can be changed to Model defined one
        data_context = deepcopy(payload.get("@context", self.model_context.iri if self.model_context else None))
        if not isinstance(data_context, list):
            data_context = [data_context]
        if self.store_context in data_context:
            data_context.remove(self.store_context)
        data_context = data_context[0] if len(data_context) == 1 else data_context
        metadata = dict()
        data = dict()
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
        if not hasattr(resource, "id") and kwargs and 'id' in kwargs.keys():
            resource.id = kwargs.get("id")
        return resource
