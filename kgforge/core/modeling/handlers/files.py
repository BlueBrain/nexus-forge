from kgforge.core.commons.actions import LazyAction


# FIXME FIXME FIXME


class FilesHandler:

    def __init__(self, forge) -> None:
        self.forge = forge

    def as_resource(self, path: str) -> LazyAction:
        return LazyAction(self.forge.store.upload, path=path)
