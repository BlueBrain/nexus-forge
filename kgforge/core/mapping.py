from pathlib import Path
from typing import Any, Dict, Iterator, Sequence, Union

import hjson

from kgforge.core.commons import Hjson
from kgforge.core.models.resources import Resource, Resources


class Mapper:

    def __init__(self, forge, mapping: Hjson) -> None:
        self.forge = forge
        self.mapping: Dict = hjson.loads(mapping)
        self.reader = None

    def apply(self, data: Any) -> Union[Resource, Resources]:
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
