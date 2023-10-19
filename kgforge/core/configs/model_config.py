import copy
import dataclasses
from typing import Dict, Optional, Union, ClassVar, List, Type

from kgforge.core.configs.config import Config
from kgforge.core.configs.store_based_config import StoreBasedConfig
from kgforge.core.configs.store_config import StoreConfig


@dataclasses.dataclass(init=True)
class ModelContextConfig(Config):
    @staticmethod
    def merge_config(
            configuration_1: Union['ModelContextConfig', Dict],
            configuration_2: Union['ModelContextConfig', Dict],
            first_into_second=False, **kwargs
    ):

        # context_endpoint = context_dict.get("endpoint", model_store_config.endpoint)
        # context_token = context_dict.get("token", model_store_config.token)
        # context_bucket = context_dict.get("bucket", model_store_config.bucket)
        #
        # if (
        #         context_endpoint != model_store_config.endpoint
        #         or context_token != model_store_config.token
        #         or context_bucket != model_store_config.bucket
        # ):
        #
        #     context_config = copy.deepcopy(model_store_config)
        #     context_config.token = context_token
        #     context_config.endpoint = context_endpoint
        #     context_config.bucket = context_bucket
        #     return context_config

        return None

    iri: str
    source: Optional['StoreConfig'] = None

    ATTRIBUTES = ["iri", "source"]

    def __eq__(self, other):
        return self.iri == other.iri and self.source == other.source


@dataclasses.dataclass(init=True)
class ModelConfig(StoreBasedConfig):
    name: Optional[str] = None
    default: Optional[bool] = None
    origin: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig', Dict]] = None
    context: Optional[Union[Dict, ModelContextConfig]] = None

    ATTRIBUTES_FLAT: ClassVar[List] = ["default", "name", "origin"]
    ATTRIBUTES = ATTRIBUTES_FLAT + ["source", "context"]

    def __eq__(self, other):
        return self.default == other.default and self.name == other.name and self.origin == \
            other.origin and self.source == other.source and self.context == other.context

    @staticmethod
    def merge_config(
            configuration_1: Union['ModelConfig', Dict],
            configuration_2: Union['ModelConfig', Dict],
            first_into_second=False, **kwargs
    ) -> 'ModelConfig':

        """
        Merges configuration of a model using information provided in a complete configuration
        and parameters passed by initializing a KnowledgeGraphForge instance
        """

        new_configuration = ModelConfig()

        for val in ModelConfig.ATTRIBUTES_FLAT:
            setattr(
                new_configuration, val,
                Config.from_first_else_second(
                    val, configuration_1, configuration_2
                )
            )

        # Deal with context
        context_temp: Dict = Config.from_first_else_second(
            "context", configuration_1, configuration_2, as_dict=True
        )

        new_configuration.context = ModelContextConfig(
            iri=context_temp.get("iri", None),
            source=context_temp.get("source", None)
        ) if context_temp is not None else None

        # Deal with source
        if new_configuration.origin == "store":

            # Model store config building
            new_configuration.source = ModelConfig.merge_store_config(
                store_configurations=kwargs.get("store_configurations"),
                configuration_1=configuration_1,
                configuration_2=configuration_2
            )

            # Model context store config building
            if new_configuration.context:
                new_configuration.context.source = \
                    ModelConfig.merge_store_config_for_model_context(
                        model_store_config=new_configuration.source,
                        context_dict=context_temp
                    )
        else:
            new_configuration.source = Config.from_first_else_second(
                "source", configuration_1, configuration_2
            )  # source will be a string

        return new_configuration

    @staticmethod
    def merge_store_config_for_model_context(
            model_store_config: 'StoreConfig', context_dict: Dict
    ) -> Optional[StoreConfig]:

        context_dict_cp = copy.deepcopy(context_dict)
        del context_dict_cp["iri"]
        test = StoreConfig.merge_config(context_dict_cp, model_store_config)
        if test == model_store_config:
            return None
        return test