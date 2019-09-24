from typing import Dict, List

from kgforge.core.commons.typing import ManagedData
from kgforge.core.commons.wrappers import PathsWrapper
from kgforge.core.modeling.model import Model


class ModelingInterface:

    def __init__(self, model: Model) -> None:
        self.model = model

    def prefixes(self) -> Dict[str, str]:
        return self.model.prefixes()

    def types(self) -> List[str]:
        return self.model.types()

    def template(self, type: str, only_required: bool = False) -> None:
        template = self.model.template(type, only_required)
        print(template)

    def validate(self, data: ManagedData) -> None:
        self.model.validate(data)

    def paths(self, type: str) -> PathsWrapper:
        template = self.model.template(type)
        return PathsWrapper._wrap(template)
