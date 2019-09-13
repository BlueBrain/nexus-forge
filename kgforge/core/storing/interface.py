from typing import Optional, Union

from kgforge.core.commons.typing import ManagedData
from kgforge.core.resources import Resource


class StoringInterface:

    def __init__(self, forge) -> None:
        self.forge = forge

    # [C]RUD

    def register(self, data: ManagedData) -> None:
        print("FIXME - StoringInterface.register()")

    # C[R]UD

    def retrieve(self, id: str, version: Optional[Union[int, str]] = None) -> Resource:
        print("FIXME - StoringInterface.retrieve()")
        return Resource()

    def download(self, data: ManagedData, path: str, follow: str) -> None:
        print("FIXME - StoringInterface.download()")

    # CR[U]D

    def tag_version(self, data: ManagedData, name: str) -> None:
        print("FIXME - StoringInterface.tag()")

    # CRU[D]

    def deprecate(self) -> None:
        print("FIXME - StoringInterface.deprecate()")
