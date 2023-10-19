import copy
import dataclasses
from abc import abstractmethod
from typing import Dict, Optional, Union, ClassVar, List, Type

from kgforge.core.configs.config import Config
from kgforge.core.configs.store_config import StoreConfig


class StoreBasedConfig(Config):

    @staticmethod
    @abstractmethod
    def merge_config(
            configuration_1: Union['StoreBasedConfig', Dict],
            configuration_2: Union['StoreBasedConfig', Dict],
            first_into_second=False, **kwargs
    ):
        pass

    @staticmethod
    def merge_store_config(
            store_configurations: Dict[str, StoreConfig],
            configuration_1: 'StoreBasedConfig',
            configuration_2: Dict
    ):
        """
        Builds a store config within a parent config (ModelConfig or ResolverConfig)
        using fields that are StoreConfig specific at the top level of the parent config
        """
        configuration_source: Union[str, Dict] = Config.from_first_else_second(
            "source", configuration_1, configuration_2
        )  # Dict possibly?

        if isinstance(configuration_source, str):
            store_id = configuration_source  # store config referred to by identifier
            store_update = {}

        elif isinstance(configuration_source, dict):
            store_id = configuration_source.get("id", None)  # store config referred to by dict,
            # with identifier inside + more information
            if store_id is None:
                raise Exception("Missing id in source object")
            store_update = {
                att: configuration_source.get(att)
                for att in StoreConfig.ATTRIBUTES_FLAT + StoreConfig.ATTRIBUTES_DICT
            }
        else:
            raise Exception(f"Invalid configuration type: {type(configuration_source)}")

        source = store_configurations.get(store_id, None)
        if source is None:
            raise Exception(f"Model config referencing non-existing store id {store_id}")

        return StoreConfig.merge_config(store_update, source)
