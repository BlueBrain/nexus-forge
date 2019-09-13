from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterator, Sequence, Union

import hjson

from kgforge.core import Resource, Resources
from kgforge.core.commons.typing import Hjson, ManagedData


class Mapping:

    def __init__(self, mapping: Hjson) -> None:
        self.rules: OrderedDict = hjson.loads(mapping)

    def save(self, path: str, include_context: bool = False) -> None:
        print("FIXME - Mapping.save()")

    def load(self, path: str) -> "Mapping":
        print("FIXME - Mapping.load()")
        return Mapping("")


class Mapper:

    def __init__(self, forge, mapping: Mapping) -> None:
        self.forge = forge
        self.mapping = mapping
        self.reader = None

    def apply(self, data: Any) -> ManagedData:
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
                return self.apply_many(records)
            else:
                with path.open() as f:
                    record = self.reader(f)
                    return self.apply_one(record)
        elif isinstance(data, (Sequence, Iterator)):
            return self.apply_many(data)
        else:
            return self.apply_one(data)

    def apply_many(self, records: Union[Sequence, Iterator]) -> Resources:
        # TODO Optimize.
        mapped = [self.apply_one(x) for x in records]
        return Resources(mapped)

    def apply_one(self, record: Any) -> Resource:
        raise NotImplementedError("Method should be overridden in the derived classes.")
