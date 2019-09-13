from kgforge.core.commons.typing import Hjson, ManagedData


class ModelingInterface:

    def __init__(self, forge) -> None:
        self.forge = forge

    def template(self, type: str, only_required: bool = False) -> Hjson:
        print("FIXME - ModelingInterface.template()")
        return sh.te

    def validate(self, data: ManagedData) -> None:
        print("FIXME - ModelingInterface.validate()")
