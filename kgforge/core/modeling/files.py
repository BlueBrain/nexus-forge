from kgforge.core.commons.actions import LazyAction


class FilesHandler:

    def __init__(self, forge) -> None:
        self.forge = forge

    def as_resource(self, path: str) -> LazyAction:
        print("FIXME - FilesHandler.as_resource()")
        return LazyAction()
