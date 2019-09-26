from typing import Dict, List, Tuple, Union

from pandas import DataFrame

from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData


class Converters:

    # POLICY Converters should be decorated with exceptions.catch() to deal with exceptions.

    @classmethod
    @catch
    def as_json(cls, data: ManagedData, expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        def _del_context(x: Dict) -> None:
            del x["@context"]
        if expanded:
            return cls.as_jsonld(data, False, store_metadata)
        else:
            data = cls.as_jsonld(data, True, store_metadata)
            _del_context(data) if not isinstance(data, List) else (_del_context(x) for x in data)
            return data

    @classmethod
    @catch
    def as_jsonld(cls, data: ManagedData, compacted: bool = True, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        # TODO Implement.
        raise NotImplementedError("TODO Implement")

    @classmethod
    @catch
    def as_triples(cls, data: ManagedData, store_metadata: bool = False) -> List[Tuple[str, str, str]]:
        # TODO Implement.
        raise NotImplementedError("TODO Implement")

    @classmethod
    @catch
    def as_dataframe(cls, data: ManagedData, store_metadata: bool = False) -> DataFrame:
        # TODO Implement.
        raise NotImplementedError("TODO Implement")
