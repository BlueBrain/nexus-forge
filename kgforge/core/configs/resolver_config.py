import dataclasses
from typing import Dict, Optional, Union, ClassVar, List

from kgforge.core.configs.config import Config
from kgforge.core.configs.store_config import StoreConfig


@dataclasses.dataclass(init=True)
class ResolverConfig(Config):
    resolver: Optional[str] = None
    origin: Optional[str] = None
    result_resource_mapping: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig']] = None
    resolve_with_properties: List[str] = None
    targets: Optional[Dict] = None

    ATTRIBUTES_FLAT: ClassVar[List] = [
        "resolver",
        "origin",
        "result_resource_mapping",
        "resolve_with_properties"
    ]

    def __eq__(self, other):
        return all([
            getattr(self, e) == getattr(other, e)
            for e in ResolverConfig.ATTRIBUTES_FLAT
        ]) and ResolverConfig.json_equals(self.targets, other.targets) and \
            ResolverConfig.json_equals(self.resolve_with_properties, other.resolve_with_properties)

    @staticmethod
    def merge_config(
            configuration_parameter: Optional['ResolverConfig'],
            configuration_from_file: Dict, **kwargs
    ):
        # TODO make the merging of targets BETTER

        if configuration_parameter is None:
            configuration_parameter = ResolverConfig(
                **dict(
                    (att, configuration_from_file.get(att))
                    for att in ResolverConfig.ATTRIBUTES_FLAT + ["targets"] if att is not None
                )
            )
        else:
            for val in ResolverConfig.ATTRIBUTES_FLAT + ["targets"]:
                setattr(
                    configuration_parameter, val,
                    Config.from_param_else_file(
                        val, configuration_parameter, configuration_from_file
                    )
                )

        # Reformat target
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

        # Set Source
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