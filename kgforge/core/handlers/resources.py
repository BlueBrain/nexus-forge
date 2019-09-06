from typing import Any

from kgforge.core.mapping import Mapper
from kgforge.core.models.resources import Resources


class ResourcesHandler:

    def __init__(self, forge) -> None:
        self.forge = forge

    @staticmethod
    def map_from(data: Any, mapper: Mapper) -> Resources:
        return mapper.apply(data)
