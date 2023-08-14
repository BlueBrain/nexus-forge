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
from typing import Callable, Dict, List, Optional

from kgforge.core.archetypes import Store
from kgforge.core.conversions.json import as_json


class StoreService:

    def __init__(self, store: Callable, targets: Dict[str, Dict[str, Dict[str, str]]], **store_config):
        self.sources: Dict[str, Store] = dict()
        self.filters: Dict[str, str] = dict()
        for identifier in targets:
            bucket = targets[identifier]["bucket"]
            if 'filters' in targets[identifier]:
                self.filters[identifier] = targets[identifier]["filters"]
            store_config.update(bucket=bucket)
            self.sources[identifier] = store(**store_config)
        self.deprecated_property = "https://bluebrain.github.io/nexus/vocabulary/deprecated"

    def perform_query(self, query: str, target: str, expected_fields: List[str],
                      limit: int) -> Optional[List[Dict]]:
        # FIXME: there is no way to provide a ranking among the results in the different targets
        """Executes the query in the different sources.

        Args:
            query: str, a CONSTRUCT query
            target: a target identifier, if None, the first one in the forge config file will be run
            expected_fields: a list of names of the expected fields
            limit: the maximum number of results to return

        Returns:
            List of results in JSON format
        """
        if target:
            if self.validate_target(target):
                resources = self.sources[target].sparql(query, debug=False, limit=limit)
        else:
            resources = list()
            if len(list(self.sources.values())) > 0:
                first_source = list(self.sources.values())[0]
                resources.extend(first_source.sparql(query, debug=False, limit=limit))

        if len(resources) > 0:
            return [format_response(r, expected_fields) for r in resources]
        else:
            return None


    def validate_target(self, target):
        if target and target not in self.sources:
            raise ValueError(f"Unknown target value: {target}. Supported targets are: {self.sources.keys()}")
        else:
            return True
        
    def get_context(self, resolving_context, target, filters):
        if not resolving_context:
            context = self.sources[target].model_context if target in self.sources else None
        if not context and filters:
            raise ValueError(f"No JSONLD context were provided. When resolving filters are set, a JSONLD context is needed.")
        else:
            return context

def format_response(resource, mandatory_fields):
    json_data = as_json(resource, expanded=False, store_metadata=False,
                        model_context=None, metadata_context=None, context_resolver=None)
    for field in mandatory_fields:
        if field not in json_data:
            json_data[field] = None
    return json_data
