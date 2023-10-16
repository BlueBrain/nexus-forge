from copy import deepcopy
from typing import Dict, List, Optional, Union
from uuid import uuid4

from kgforge.core.archetypes.store import StoreService
from kgforge.core.commons.context import Context
from kgforge.core.commons.execution import not_supported
from kgforge.core.wrappings.dict import wrap_dict


class DemoStoreService(StoreService):
    """Simulate a third-party library handling interactions with the database used by the store."""

    def __init__(self):
        self.records: Dict[str, Dict] = {}
        self.archives: Dict[str, Dict] = {}
        self.tags: Dict[str, int] = {}

    def create(self, data: Dict) -> Dict:
        record = self._record(data, 1, False)
        rid = record["data"]["id"]
        if rid in self.records.keys():
            raise self.RecordExists
        self.records[rid] = record
        return record

    def read(self, rid: str, version: Optional[Union[int, str]]) -> Dict:
        try:
            if version is not None:
                if isinstance(version, str):
                    tkey = self._tag_id(rid, version)
                    version = self.tags[tkey]
                akey = self._archive_id(rid, version)
                record = self.archives[akey]
            else:
                record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            return record

    def update(self, data: Dict) -> Dict:
        rid = data.get("id", None)
        try:
            record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            metadata = record["metadata"]
            if metadata["deprecated"]:
                raise self.RecordDeprecated
            version = metadata["version"]
            key = self._archive_id(rid, version)
            self.archives[key] = record
            new_record = self._record(data, version + 1, False)
            self.records[rid] = new_record
            return new_record

    def deprecate(self, rid: str) -> Dict:
        try:
            record = self.records[rid]
        except KeyError:
            raise self.RecordMissing
        else:
            metadata = record["metadata"]
            if metadata["deprecated"]:
                raise self.RecordDeprecated
            version = metadata["version"]
            key = self._archive_id(rid, version)
            self.archives[key] = record
            data = record["data"]
            new_record = self._record(data, version + 1, True)
            self.records[rid] = new_record
            return new_record

    def tag(self, rid: str, version: int, value: str) -> None:
        if rid in self.records:
            key = self._tag_id(rid, value)
            if key in self.tags:
                raise self.TagExists
            else:
                self.tags[key] = version
        else:
            raise self.RecordMissing

    def find(self, conditions: List[str]) -> List[Dict]:
        return [r for r in self.records.values()
                if all(eval(c, {}, {"x": wrap_dict(r["data"])}) for c in conditions)]

    def _record(self, data: Dict, version: int, deprecated: bool) -> Dict:
        copy = deepcopy(data)
        if "id" not in copy:
            copy["id"] = self._new_id()
        return {
            "data": copy,
            "metadata": {
                "version": version,
                "deprecated": deprecated,
            },
        }

    @staticmethod
    def _new_id() -> str:
        return str(uuid4())

    @staticmethod
    def _archive_id(rid: str, version: int) -> str:
        return f"{rid}_version={version}"

    @staticmethod
    def _tag_id(rid: str, tag: str) -> str:
        return f"{rid}_tag={tag}"

    def rewrite_uri(self, uri: str, context: Context, **kwargs) -> str:
        raise not_supported()

    class RecordExists(Exception):
        pass

    class RecordMissing(Exception):
        pass

    class RecordDeprecated(Exception):
        pass

    class TagExists(Exception):
        pass
