from typing import Callable

from kgforge.core.commons.typing import Hjson, ManagedData


class ModelingInterface:

    def __init__(self, model: Callable, model_dir: str) -> None:
        self.model = model(model_dir)

    def template(self, type: str, only_required: bool = False) -> Hjson:
        return self.model.template(type, only_required)

    def validate(self, data: ManagedData) -> None:
        self.model.validate(data)
