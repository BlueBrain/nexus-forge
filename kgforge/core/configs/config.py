import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type
from abc import abstractmethod, ABC
import json
from kgforge.core.commons.imports import import_class
# from kgforge.core.configs.store_config import StoreConfig


@dataclasses.dataclass(init=True)
class Config(ABC):

    @staticmethod
    @abstractmethod
    def merge_config(configuration: Optional['Config'], model_config: Dict, **kwargs):
        pass

    @staticmethod
    def from_param_else_file(key, config_params: 'Config', config_file: Dict):
        """
        For the field referred to by the key, retrieve its value in the first object if it's
        available, else get it from the second dictionary
        """
        return getattr(config_params, key) \
            if getattr(config_params, key) is not None \
            else config_file.get(key, None)

    @staticmethod
    def from_param_else_file_dict(key, config_params: 'Config', config_file: Dict):

        priority = getattr(config_params, key)
        template = config_file.get(key, None)

        if priority is None:
            return template
        if template is None:
            return priority

        for key in template.keys():
            template[key] = priority.get(key, template[key])
        return template

    def initialize(self, package_str):
        constructor: Type = import_class(self.name, package_str)
        return constructor(self)

    @staticmethod
    def json_equals(a, b):
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


