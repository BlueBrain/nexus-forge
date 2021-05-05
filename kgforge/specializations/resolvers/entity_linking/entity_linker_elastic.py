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
from pathlib import Path
from typing import Callable, Dict, List, Any

from kgforge.core.commons.execution import not_supported
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers.entity_linking import EntityLinker
from kgforge.specializations.resolvers.entity_linking.service.entity_linking_elastic_service import EntityLinkerElasticService


class EntityLinkerElastic(EntityLinker):

    def __init__(self, source: str, targets: List[Dict[str, str]], result_resource_mapping: str,
                 **source_config) -> None:
        super().__init__(source, targets, result_resource_mapping, **source_config)

    @property
    def mapping(self) -> Callable:
        return DictionaryMapping

    @property
    def mapper(self) -> Callable:
        return DictionaryMapper

    @staticmethod
    def _service_from_directory(dirpath: Path, targets: Dict[str, str]) -> Any:
        not_supported()

    @staticmethod
    def _service_from_store(store: Callable, targets: Dict[str, str], **store_config) -> EntityLinkerElasticService:
        encoder = store_config.pop("encoder")
        encoder_url = encoder["source"]
        encoder_result_resource_mapping = encoder["result_resource_mapping"]
        return EntityLinkerElasticService(store, targets, encoder_url, encoder_result_resource_mapping, **store_config)
