#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

from copy import deepcopy
from yaml import safe_load

from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Type
from kgforge.core.commons.files import load_file_as_byte

from kgforge.core import Resource, KnowledgeGraphForge
from kgforge.core.archetypes import Mapping, Model, Resolver, Store
from kgforge.core.configs.model_config import ModelConfig
from kgforge.core.configs.store_config import StoreConfig
from kgforge.core.configs.resolver_config import ResolverConfig
from kgforge.core.configs.config import Config


class KnowledgeGraphForgeMulti(KnowledgeGraphForge):

    # POLICY Class name should be imported in the corresponding module __init__.py.

    # No catching of exceptions so that no incomplete instance is created if an error occurs.
    # This is a best practice in Python for __init__().

    @staticmethod
    def load_configurations(
            configuration: Union[str, Dict],
            model_configurations: Optional[Dict[str, ModelConfig]] = None,
            store_configurations: Optional[Dict[str, StoreConfig]] = None,
            resolver_configurations: Dict[str, List[ResolverConfig]] = None,
            selected_model: Optional[str] = None,
            selected_store: Optional[str] = None,
    ) -> Tuple[ModelConfig, StoreConfig, Dict[str, List[ResolverConfig]], Optional[Any]]:

        if isinstance(configuration, str):
            config_data = load_file_as_byte(configuration)
            config_data = config_data.decode("utf-8")
            config = safe_load(config_data)
        else:
            config = deepcopy(configuration)

        # Store.
        store_configurations_from_file: Dict[str, Dict] = config.pop("Store")

        store_configurations = dict(
            (
                key,
                StoreConfig.merge_config(
                    store_configurations.get(key) if store_configurations else None,
                    store_configurations_from_file.get(key)
                )
            )
            for key in store_configurations_from_file.keys()
        )

        # Model.
        model_configurations_from_file: Dict[str, Dict] = config.pop("Model")

        model_configurations = dict(
            (key, ModelConfig.merge_config(
                model_configurations.get(key) if model_configurations else None,
                model_configurations_from_file.get(key),
                store_configurations=store_configurations
            ))
            for key in model_configurations_from_file.keys()
        )

        def get_selected(key, selected_parameter, dict_values: [Dict[str, Config]]) -> Config:
            if selected_parameter is not None:
                return dict_values[selected_parameter]

            if config.get(key, None) is not None:
                return dict_values[config.get(key, None)]
            else:
                return next(e for (k, e) in dict_values.items() if e.default)

        selected_model_config: ModelConfig = get_selected(
            "selected_model", selected_model, model_configurations
        )

        selected_store_config: StoreConfig = get_selected(
            "selected_store", selected_store, store_configurations
        )

        # Resolvers.
        resolvers_configurations_from_file = config.pop("Resolvers", None)

        if resolvers_configurations_from_file is not None:

            resolver_configurations = dict(
                (
                    key,
                    [
                        ResolverConfig.merge_config(
                            resolver_configurations.get(key) if resolver_configurations else None,
                            resolvers_configurations_from_file.get(key)[0],
                            store_configurations=store_configurations
                        )
                    ]  # TODO handle array
                )
                for key in resolvers_configurations_from_file.keys()
            )
        else:
            resolver_configurations = None

        # Formatters.
        formatters = config.pop("Formatters", None)

        return selected_model_config, selected_store_config, resolver_configurations, formatters

    def __init__(
            self, configuration: Union[str, Dict],
            model_configurations: Optional[Dict[str, ModelConfig]] = None,
            store_configurations: Optional[Dict[str, StoreConfig]] = None,
            resolver_configurations: Dict[str, ResolverConfig] = None,
            selected_model: Optional[str] = None,
            selected_store: Optional[str] = None,
            debug: bool = False
    ):

        selected_model_config, selected_store_config, resolver_configs, formatters = \
            KnowledgeGraphForgeMulti.load_configurations(
                configuration, model_configurations, store_configurations,
                resolver_configurations, selected_model, selected_store
            )

        self._model: Model = selected_model_config.initialize("models")
        self._store: Store = selected_store_config.initialize("stores")
        self._store.model_context = self._model.context()  # TODO figure out why

        def _init_resolver(config: ResolverConfig) -> Tuple[str, Resolver]:
            resolver = config.initialize("resolvers")
            return type(resolver).__name__, resolver

        self._resolvers = {
            scope: dict(_init_resolver(x) for x in configs)
            for scope, configs in resolver_configs.items()
        } if resolver_configs is not None else None

        # Formatters.
        self._formatters: Optional[Dict[str, str]] = formatters


if __name__ == "__main__":

    # token = getpass.getpass()

    args = dict(
        configuration="../test_multi.yml",
        store_config={
            "store_1": StoreConfig()
        }
    )

    e = KnowledgeGraphForgeMulti(**args)
