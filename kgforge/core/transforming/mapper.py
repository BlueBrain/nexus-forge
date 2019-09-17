from pathlib import Path
from typing import Any, Iterator, Sequence, Union

from kgforge.core import Resource, Resources
from kgforge.core.commons.attributes import should_be_overridden
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
                # Could be optimized by overriding the method in the specialization.
                records = []
                for x in path.iterdir():
                    with x.open() as f:
                        records.append(self.reader(f))
                return self._map_many(records, mapping)
            else:
                with path.open() as f:
                    record = self.reader(f)
                    return self._map_one(record, mapping)
        elif isinstance(data, (Sequence, Iterator)):
            return self._map_many(data, mapping)
        else:
            return self._map_one(data, mapping)

    def _map_many(self, records: Union[Sequence, Iterator], mapping: Mapping) -> Resources:
        # Could be optimized by overriding the method in the specialization.
        mapped = [self._map_one(x, mapping) for x in records]
        return Resources(mapped)

    def _map_one(self, record: Any, mapping: Mapping) -> Resource:
        should_be_overridden()
