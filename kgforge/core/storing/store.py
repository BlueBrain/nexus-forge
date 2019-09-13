from kgforge.core import Resource, Resources
from kgforge.core.commons.actions import Actions, _run
from kgforge.core.commons.typing import ManagedData


class Store:

    def __init__(self) -> None:
        pass

    # [C]RUD

    def register(self, data: ManagedData) -> None:
        if isinstance(data, Resources):
            return self.register_many(data)
        else:
            _run(self.register_one, "_synchronized", data)
            print(data._last_action)

    def register_many(self, resources: Resources) -> None:
        # FIXME Optimize.
        for x in resources:
            _run(self.register_one, "_synchronized", x)
        print(Actions.from_resources(resources))

    def register_one(self, resource: Resource) -> bool:
        raise NotImplementedError("Method should be overridden in the derived classes.")

    # C[R]UD

    pass

    # CR[U]D

    pass

    # CRU[D]

    pass
