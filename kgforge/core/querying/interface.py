from kgforge.core import Resources


class QueryingInterface:

    def __init__(self, forge) -> None:
        self.forge = forge

    def search(self, *args) -> Resources:
        print("FIXME - QueryingInterface.search()")
        return Resources([])
