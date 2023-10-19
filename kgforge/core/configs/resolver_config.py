import dataclasses
from typing import Dict, Optional, Union, ClassVar, List

from kgforge.core.configs.config import Config
from kgforge.core.configs.store_based_config import StoreBasedConfig
from kgforge.core.configs.store_config import StoreConfig


@dataclasses.dataclass(init=True)
class ResolverConfig(StoreBasedConfig):
    resolver: Optional[str] = None
    origin: Optional[str] = None
    result_resource_mapping: Optional[str] = None
    source: Optional[Union[str, 'StoreConfig', Dict]] = None
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
            configuration_1: Optional['ResolverConfig'],
            configuration_2: Dict, **kwargs
    ):
        # TODO make the merging of targets BETTER

        new_configuration = ResolverConfig()

        for val in ResolverConfig.ATTRIBUTES_FLAT + ["targets"]:
            setattr(
                new_configuration, val,
                Config.from_first_else_second(
                    val, configuration_1, configuration_2
                )
            )

        # Reformat target

        if new_configuration.targets is not None:
            new_target_dict = {}

            for target in new_configuration.targets:
                if "filters" in target:
                    # reshape filters to match query filters
                    filters = {f["path"]: f["value"] for f in target["filters"]}
                else:
                    filters = None

                new_target_dict[target["identifier"]] = {
                    "bucket": target["bucket"],
                    "filters": filters
                }

            new_configuration.targets = new_target_dict

        # Set Source
        if new_configuration.origin == "store":
            store_configurations: Dict[str, StoreConfig] = kwargs.get("store_configurations")

            # Resolver store config building
            new_configuration.source = ResolverConfig.merge_store_config(
                store_configurations, configuration_1, configuration_2
            )
        else:
            new_configuration.source = Config.from_first_else_second(
                "source", configuration_1, configuration_2
            )

        return new_configuration

