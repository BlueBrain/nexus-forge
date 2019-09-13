from typing import Optional

from kgforge.core.commons.actions import LazyAction


class OntologiesHandler:

    def __init__(self, forge) -> None:
        self.forge = forge

    def as_resource(self, label: str, hint: Optional[str] = None) -> LazyAction:
        print("FIXME - OntologiesHandler.as_resource()")
        return LazyAction()
