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
from typing import Dict, List, Callable

from kgentitylinkingsklearn import EntityLinkerServiceSkLearn
from kgforge.core.commons.actions import LazyAction
from kgforge.specializations.mappers import DictionaryMapper
from kgforge.specializations.mappings import DictionaryMapping
from kgforge.specializations.resolvers import EntityLinker


class EntityLinkerSkLearn(EntityLinker):

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
    def _service_from_directory(dirpath: Path, targets: Dict[str, str], ** source_config) -> Dict[str, LazyAction]:
        # FIXME: the same model is loaded multiple times if provided for multiple targets
        return {target: LazyAction(EntityLinkerServiceSkLearn.from_pretrained, dirpath, filename) for target, filename in
                targets.items()}
