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

from rdflib.plugins.sparql.parser import Query

from kgforge.core.archetypes import Store
from kgforge.core.commons.strategies import ResolvingStrategy
from kgforge.core.conversions.json import as_json


class StoreService:

    def __init__(self, store: Callable, targets: Dict[str, str], **store_config):
        self.sources: Dict[str, Store] = dict()
        for target, bucket in targets.items():
            store_config.update(bucket=bucket)
            self.sources[target] = store(**store_config)
        self.deprecated_property = "https://bluebrain.github.io/nexus/vocabulary/deprecated"

    def perform_query(self, query: str, target: str, expected_fields: List[str],
                      limit: int) -> Optional[List[Dict]]:
        # FIXME: there is no way to provide a ranking among the results in the different targets
        """Executes the query in the different sources.

        Args:
            query: str, a CONSTRUCT query
            target: a target identifier, if None, it will runt the query in all available targets
            expected_fields: a list of names of the expected fields
            limit: the maximum number of results to return

        Returns:
            List of results in JSON format
        """
        if target:
            if target in self.sources:
                resources = self.sources[target].sparql(query, debug=False, limit=limit)
            else:
                raise ValueError(f"Target {target} not identified")
        else:
            resources = list()
            for source in self.sources.values():
                resources.extend(source.sparql(query, debug=False, limit=limit))

        if len(resources) > 0:
            return [format_response(r, expected_fields) for r in resources]
        else:
            return None


def format_response(resource, mandatory_fields):
    json_data = as_json(resource, expanded=False, store_metadata=False,
                        model_context=None, metadata_context=None, context_resolver=None)
    for field in mandatory_fields:
        if field not in json_data:
            json_data[field] = None
    return json_data
