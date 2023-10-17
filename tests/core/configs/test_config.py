from typing import Dict
from kgforge.core.configs.model_config import ModelConfig, ModelContextConfig
from kgforge.core.configs.store_config import StoreConfig
from kgforge.core.forge_multi import KnowledgeGraphForgeMulti
import os
import pytest


def test_load_config_model():

    configuration = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../data/forge_multi/test_multi.yml"
    )

    new_endpoint = "https://bbp.epfl.ch/neurosciencegraph/data/views/aggreg-sp/dataset"

    store_config = {
        "store_1": StoreConfig(
            searchendpoints={
                "sparql": {
                    "endpoint": new_endpoint
                }
            },
            bucket="bbp/atlas"
        )
    }

    model_config = {
        "model_1": ModelConfig(

        )
    }

    selected_model_config, selected_store_config, resolver_configs, formatters = \
        KnowledgeGraphForgeMulti.load_configurations(
            configuration,
            model_configurations=None,
            store_configurations=store_config,
            resolver_configurations=None,
            selected_model=None,
            selected_store=None
        )

    print(selected_store_config.searchendpoints)

