from kgforge.core import Resource, Resources
from kgforge.core.commons.actions import Actions, _run
from kgforge.core.commons.typing import Hjson, ManagedData


class Model:

    def __init__(self, model_dir: str) -> None:
        self.model_dir = model_dir

    def template(self, type: str, only_required: bool = False) -> Hjson:
        raise NotImplementedError("Method should be overridden in the derived classes.")

    def validate(self, data: ManagedData) -> None:
        if isinstance(data, Resources):
            return self.validate_many(data)
        else:
            _run(self.validate_one, "_validated", data)
            print(data._last_action)

    def validate_many(self, resources: Resources) -> None:
        # FIXME Optimize.
        for x in resources:
            _run(self.validate_one, "_validated", x)
        print(Actions.from_resources(resources))

    def validate_one(self, resource: Resource) -> bool:
        raise NotImplementedError("Method should be overridden in the derived classes.")
