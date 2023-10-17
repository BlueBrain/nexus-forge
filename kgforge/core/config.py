import copy
import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type
from abc import abstractmethod, ABC

from kgforge.core.commons.imports import import_class


@dataclasses.dataclass(init=True)
class Config(ABC):
    default: Optional[bool] = None
    name: Optional[str] = None

    @staticmethod
    @abstractmethod
    def load_config(configuration: Optional['Config'], model_config: Dict, **kwargs):
        pass

    @staticmethod
    def from_param_else_file(key, config_params, config_file):
        return getattr(config_params, key) \
            if getattr(config_params, key) is not None \
            else config_file.get(key, None)

    @staticmethod
    def build_store_config_for_else(
            store_configurations, configuration_parameter, configuration_from_file
    ):

        configuration_source: Union[str, Dict] = Config.from_param_else_file(
            "source", configuration_parameter, configuration_from_file
        )

        if isinstance(configuration_source, str):
            store_id = configuration_source
            store_update = {}
        else:
            store_id = configuration_source.get("id", None)
            if store_id is None:
                raise Exception("Missing id in source object")
            store_update = {
                att: configuration_source.get(att)
                for att in StoreConfig.ATTRIBUTES
            }

        source = store_configurations.get(configuration_source, None)
        if source is None:
            raise Exception(f"Model config referencing non-existing store id {store_id}")

        return StoreConfig.load_config(source, store_update)

    def initialize(self, package_str):
        constructor: Type = import_class(self.name, package_str)
        return constructor(self)


@dataclasses.dataclass(init=True)
class ModelContextConfig:
    iri: str
    source: Optional['StoreConfig'] = None


@dataclasses.dataclass(init=True)
class ModelConfig(Config):
    origin: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig']] = None
    context: Optional[ModelContextConfig] = None

    @staticmethod
    def load_config(
            configuration_parameter: Optional['ModelConfig'],
            configuration_from_file: Dict, **kwargs
    ) -> 'ModelConfig':

        attributes = ["default", "name", "origin", None, None]

        if configuration_parameter is None:
            configuration_parameter = ModelConfig(
                **dict(
                    (att, configuration_from_file.get(att))
                    for att in attributes if att is not None
                )
            )
        else:
            for val in attributes:
                setattr(
                    configuration_parameter, val,
                    Config.from_param_else_file(
                        val, configuration_parameter, configuration_from_file
                    )
                )

        context_temp = Config.from_param_else_file(
            "context", configuration_parameter, configuration_from_file
        )

        configuration_parameter.context = ModelContextConfig(
            iri=context_temp.get("iri", None), source=None
        ) if context_temp is not None else None

        if configuration_parameter.origin == "store":
            store_configurations: Dict[str, StoreConfig] = kwargs.get("store_configurations")

            # Model store config building
            configuration_parameter.source = ModelConfig.build_store_config_for_else(
                store_configurations, configuration_parameter, configuration_from_file
            )

            # Model context store config building
            if configuration_parameter.context:
                configuration_parameter.context.source = ModelConfig. \
                    build_store_config_for_model_context(
                        model_store_config=configuration_parameter.source,
                        context_dict=context_temp
                    )
        else:
            configuration_parameter.source = Config.from_param_else_file(
                "source", configuration_parameter, configuration_from_file
            )

        return configuration_parameter

    @staticmethod
    def build_store_config_for_model_context(
            model_store_config: 'StoreConfig', context_dict: Dict
    ):

        context_endpoint = context_dict.get("endpoint", model_store_config.endpoint)
        context_token = context_dict.get("token", model_store_config.token)
        context_bucket = context_dict.get("bucket", model_store_config.bucket)

        if (context_endpoint != model_store_config.endpoint
                or context_token != model_store_config.token
                or context_bucket != model_store_config.bucket):
            context_config = copy.deepcopy(model_store_config)
            context_config.token = context_token
            context_config.endpoint = context_endpoint
            context_config.bucket = context_bucket

            return context_config

        return None


@dataclasses.dataclass(init=True)
class ResolverConfig(Config):
    resolver: Optional[str] = None
    origin: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig']] = None
    targets: Optional[Dict] = None
    resolve_with_properties: List[str] = None
    result_resource_mapping: Optional[str] = None

    @staticmethod
    def load_config(
            configuration_parameter: Optional['ResolverConfig'],
            configuration_from_file: Dict, **kwargs
    ):

        attributes = ["resolver", "origin", "targets", "resolve_with_properties",
                      "result_resource_mapping"]

        if configuration_parameter is None:
            configuration_parameter = ResolverConfig(
                **dict(
                    (att, configuration_from_file.get(att))
                    for att in attributes if att is not None
                )
            )
        else:
            for val in attributes:
                setattr(
                    configuration_parameter, val,
                    Config.from_param_else_file(
                        val, configuration_parameter, configuration_from_file
                    )
                )

        new_target_dict = {}

        for target in configuration_parameter.targets:
            if "filters" in target:
                # reshape filters to match query filters
                filters = {f["path"]: f["value"] for f in target["filters"]}
            else:
                filters = None

            new_target_dict[target["identifier"]] = {
                "bucket": target["bucket"],
                "filters": filters
            }

        configuration_parameter.targets = new_target_dict

        if configuration_parameter.origin == "store":
            store_configurations: Dict[str, StoreConfig] = kwargs.get("store_configurations")

            # Resolver store config building
            configuration_parameter.source = ResolverConfig.build_store_config_for_else(
                store_configurations, configuration_parameter, configuration_from_file
            )
        else:
            configuration_parameter.source = Config.from_param_else_file(
                "source", configuration_parameter, configuration_from_file
            )

        return configuration_parameter


@dataclasses.dataclass(init=True)
class StoreConfig(Config):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    searchendpoints: Optional[Dict] = None
    bucket: Optional[str] = None
    token: Optional[str] = None
    versioned_id_template: Optional[str] = None
    file_resource_mapping: Optional[str] = None
    max_connection: Optional[int] = None
    vocabulary: Optional[Dict] = None

    ATTRIBUTES: ClassVar[List] = [
        "name", "endpoint", "searchendpoints",
        "bucket", "token", "versioned_id_template",
        "file_resource_mapping", "max_connection", "vocabulary", "default"
    ]
    # model_context: Optional[Context] = None

    @staticmethod
    def load_config(configuration: Optional['StoreConfig'], model_config: Dict, **kwargs):

        if configuration is None:
            return StoreConfig(*{att: model_config.get(att) for att in StoreConfig.ATTRIBUTES})

        for val in StoreConfig.ATTRIBUTES:
            setattr(
                configuration, val,
                getattr(configuration, val, None)
                if getattr(configuration, val, None) is not None
                else model_config.get(val, None)
            )

        return configuration
