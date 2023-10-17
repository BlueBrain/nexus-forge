import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type

from kgforge.core.configs.config import Config


@dataclasses.dataclass(init=True)
class StoreConfig(Config):
    default: Optional[bool] = None
    name: Optional[str] = None
    endpoint: Optional[str] = None
    bucket: Optional[str] = None
    token: Optional[str] = None
    versioned_id_template: Optional[str] = None
    file_resource_mapping: Optional[str] = None
    max_connection: Optional[int] = None
    Accept: Optional[str] = None
    Content_Type: Optional[str] = None  # TODO different because - is not legal
    searchendpoints: Optional[Dict] = None
    vocabulary: Optional[Dict] = None
    files_upload: Optional[Dict] = None
    files_download: Optional[Dict] = None
    params: Optional[Dict] = None

    ATTRIBUTES_DICT: ClassVar[List] = [
        "searchendpoints", "vocabulary", "files_upload", "files_download", "params"
    ]

    ATTRIBUTES_FLAT: ClassVar[List] = [
        "name",
        "endpoint",
        "bucket",
        "token",
        "versioned_id_template",
        "file_resource_mapping",
        "max_connection",
        "default",
        "Accept",
        "Content_Type",
    ]

    def __eq__(self, other):
        return all([
            getattr(self, e) == getattr(other, e)
            for e in StoreConfig.ATTRIBUTES_FLAT
        ]) and all([
            StoreConfig.json_equals(getattr(self, e), getattr(other, e))
            for e in StoreConfig.ATTRIBUTES_DICT
        ])

    @staticmethod
    def merge_config(configuration: Optional['StoreConfig'], store_config: Dict, **kwargs):

        if configuration is None:
            return StoreConfig(*{att: store_config.get(att) for att in StoreConfig.ATTRIBUTES_FLAT})

        for val in StoreConfig.ATTRIBUTES_FLAT:
            setattr(
                configuration, val,
                Config.from_param_else_file(val, configuration, store_config)
            )

        for val in StoreConfig.ATTRIBUTES_DICT:
            setattr(
                configuration, val,
                Config.from_param_else_file_dict(val, configuration, store_config)
            )

        return configuration
