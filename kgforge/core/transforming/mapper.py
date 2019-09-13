from pathlib import Path
from typing import Any, Iterator, Sequence, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import ManagedData
from kgforge.core.transforming import Mapping


class Mapper:
    reader = None

    def __init__(self, forge) -> None:
        self.forge = forge

    def map(self, data: Any, mapping: Mapping) -> ManagedData:
        if isinstance(data, str):
            if self.reader is None:
                raise NotImplementedError("Mapper reader should be set in derived classes.")
            path = Path(data)
            if path.is_dir():
                # TODO Optimize.
                records = []
                for x in path.iterdir():
                    with x.open() as f:
                        records.append(self.reader(f))
                return self.map_many(records, mapping)
            else:
                with path.open() as f:
                    record = self.reader(f)
                    return self.map_one(record, mapping)
        elif isinstance(data, (Sequence, Iterator)):
            return self.map_many(data, mapping)
        else:
            return self.map_one(data, mapping)

    def map_many(self, records: Union[Sequence, Iterator], mapping: Mapping) -> Resources:
        # TODO Optimize.
        mapped = [self.map_one(x, mapping) for x in records]
        return Resources(mapped)

    def map_one(self, record: Any, mapping: Mapping) -> Resource:
        raise NotImplementedError("Method should be overridden in the derived classes.")
