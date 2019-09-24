from typing import Dict, List, Tuple, Union

from pandas import DataFrame

from kgforge.core.commons.exceptions import catch
from kgforge.core.commons.typing import ManagedData, as_list_if_not


class Converters:

    # POLICY Converters should be decorated with exceptions.catch() to deal with exceptions.

    @classmethod
    @catch
    def as_json(cls, data: ManagedData, expanded: bool = False, store_metadata: bool = False) -> Union[Dict, List[Dict]]:
        if expanded:
            return cls.as_jsonld(data, False, store_metadata)
        else:
            data = cls.as_jsonld(data, True, store_metadata)
            for x in as_list_if_not(data):
                del x["@context"]
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
        # FIXME Implement.
        raise NotImplementedError("FIXME Implement")
