from core.transforming import Mapper, Mapping


class TableMapper(Mapper):

    def __init__(self, forge, mapping: Mapping) -> None:
        super().__init__(forge, mapping)
        self.reader = None
