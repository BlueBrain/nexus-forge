import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type
from abc import abstractmethod, ABC
import json
from kgforge.core.commons.imports import import_class


@dataclasses.dataclass(init=True)
class Config(ABC):

    ATTRIBUTES: ClassVar[List]

    @staticmethod
    @abstractmethod
    def merge_config(
            configuration_1: Union['Config', Dict],
            configuration_2: Union['Config', Dict],
            first_into_second=False, **kwargs
    ):
        pass

    @staticmethod
    def get_from_dict_or_config(key, o):
        if o is None:
            return None

        from_dict = lambda d: d.get(key, None)
        from_config = lambda c: getattr(c, key, None)
        return from_config(o) if isinstance(o, Config) else from_dict(o)

    @staticmethod
    def from_first_else_second(
            key,
            config_1: Optional[Union['Config', Dict]],
            config_2: Optional[Union['Config', Dict]],
            as_dict=False
    ):
        """
              For the field referred to by the key, retrieve its value in the first value if it's
              available, else get it from the second value
        """

        first_v = Config.get_from_dict_or_config(key, config_1)
        second_v = Config.get_from_dict_or_config(key, config_2)

        if not as_dict:
            return first_v if first_v is not None else second_v

        if first_v is None:
            return second_v
        if second_v is None:
            return first_v

        def get_keys(o: Union['Config', Dict]):
            k = o.keys() if isinstance(o, dict) else o.ATTRIBUTES
            return set(k)

        combined_keys = set(get_keys(first_v)).union(get_keys(second_v))

        new_dict = {}
        for key in combined_keys:
            first_e = Config.get_from_dict_or_config(key, first_v)
            second_e = Config.get_from_dict_or_config(key, second_v)
            new_dict[key] = first_e if first_e is not None else second_e

        return new_dict

    def initialize(self, package_str):
        constructor: Type = import_class(self.name, package_str)
        return constructor(self)

    @staticmethod
    def json_equals(a, b):
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


