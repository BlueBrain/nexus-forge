from typing import Union

from kgforge.core.commons.typing import DirPath, URL
from kgforge.core.modeling.model import Model
from kgforge.core.storing import Store


class Neuroshapes(Model):

    def __init__(self, source: Union[DirPath, URL, Store]) -> None:
        super().__init__(source)

    # FIXME Implement.
