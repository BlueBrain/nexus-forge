from kgforge.core.handlers.resources import ResourcesHandler


class Forge:

    # FIXME THIS IS NOT THE INTENDED IMPLEMENTATION.
    # FIXME Add necessary arguments.
    def __init__(self) -> None:
        self.resources = ResourcesHandler(self)
