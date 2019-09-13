from kgforge.core.transforming import Mapper


class TableMapper(Mapper):
    reader = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("FIXME - TableMapper")
