from kgforge.core.commons.actions import LazyAction
from kgforge.core.storing.store import Store


class FilesHandler:

    def __init__(self, store: Store) -> None:
        self._store = store

    def as_resource(self, path: str) -> LazyAction:
        return LazyAction(self._store.upload, path)
