from typing import Dict, List

from kgforge.core.commons.typing import Hjson, ManagedData
from kgforge.core.commons.wrappers import PathsWrapper, wrap_paths
from kgforge.core.modeling.model import Model


class ModelingInterface:

    def __init__(self, model: Model) -> None:
        self.model = model

    def prefixes(self) -> Dict[str, str]:
        return self.model.prefixes()

    def types(self) -> List[str]:
        return self.model.types()

    def template(self, type: str, only_required: bool = False) -> Hjson:
        return self.model.template(type, only_required)

    def validate(self, data: ManagedData) -> None:
        self.model.validate(data)

    def paths(self, type: str) -> PathsWrapper:
        return wrap_paths(self.template(type))
