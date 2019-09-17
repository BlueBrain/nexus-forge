from kgforge.core.transforming import Mapper


class ResourceMapper(Mapper):
    reader = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("FIXME - ResourceMapper")
