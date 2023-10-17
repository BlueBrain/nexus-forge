import copy
import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type

from kgforge.core.configs.config import Config
from kgforge.core.configs.store_config import StoreConfig


@dataclasses.dataclass(init=True)
class ModelContextConfig:
    iri: str
    source: Optional['StoreConfig'] = None

    def __eq__(self, other):
        return self.iri == other.iri and self.source == other.source


@dataclasses.dataclass(init=True)
class ModelConfig(Config):
    name: Optional[str] = None
    default: Optional[bool] = None
    origin: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig']] = None
    context: Optional[ModelContextConfig] = None

    ATTRIBUTES_FLAT: ClassVar[List] = ["default", "name", "origin"]

    def __eq__(self, other):
        return self.default == other.default and self.name == other.name and self.origin == \
            other.origin and self.source == other.source and self.context == other.context

    @staticmethod
    def merge_config(
            configuration_parameter: Optional['ModelConfig'],
            configuration_from_file: Dict, **kwargs
    ) -> 'ModelConfig':

        """
        Merges configuration of a model using information provided in a complete configuration
        and parameters passed by initializing a KnowledgeGraphForge instance
        """

        if configuration_parameter is None:
            configuration_parameter = ModelConfig(
                **dict(
                    (att, configuration_from_file.get(att))
                    for att in ModelConfig.ATTRIBUTES_FLAT if att is not None
                )
            )
        else:
            for val in ModelConfig.ATTRIBUTES_FLAT:
                setattr(
                    configuration_parameter, val,
                    Config.from_param_else_file(
                        val, configuration_parameter, configuration_from_file
                    )
                )

        # Deal with context
        context_temp = Config.from_param_else_file(
            "context", configuration_parameter, configuration_from_file
        )

        configuration_parameter.context = ModelContextConfig(
            iri=context_temp.get("iri", None), source=None
        ) if context_temp is not None else None

        # Deal with source
        if configuration_parameter.origin == "store":
            store_configurations: Dict[str, StoreConfig] = kwargs.get("store_configurations")

            # Model store config building
            configuration_parameter.source = ModelConfig.build_store_config_for_else(
                store_configurations, configuration_parameter, configuration_from_file
            )

            # Model context store config building
            if configuration_parameter.context:
                # TODO Can a model store be completely different from the context store?
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

        if (
                context_endpoint != model_store_config.endpoint
                or context_token != model_store_config.token
                or context_bucket != model_store_config.bucket
        ):

            context_config = copy.deepcopy(model_store_config)
            context_config.token = context_token
            context_config.endpoint = context_endpoint
            context_config.bucket = context_bucket

            return context_config

        return None

    @staticmethod
    def build_store_config_for_else(
            store_configurations, configuration_parameter, configuration_from_file
    ):
        """
        Builds a store config within a parent config (ModelConfig or ResolverConfig)
        using fields that are StoreConfig specific at the top level of the parent config
        """
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
                for att in StoreConfig.ATTRIBUTES_FLAT
            }

        # TODO non-flat merge of store attributes
        source = store_configurations.get(configuration_source, None)
        if source is None:
            raise Exception(f"Model config referencing non-existing store id {store_id}")

        return StoreConfig.merge_config(source, store_update)
