from kgforge.core.commons.typing import ManagedData
from kgforge.core.storing import Store


class StoringInterface:

    def __init__(self, store: Store) -> None:
        self.store = store

    def register(self, data: ManagedData) -> None:
        self.store.register(data, update=False)

    def update(self, data: ManagedData) -> None:
        self.store.update(data)

    def tag_version(self, data: ManagedData, value: str) -> None:
        self.store.tag(data, value)

    def deprecate(self, data: ManagedData) -> None:
        self.store.deprecate(data)
