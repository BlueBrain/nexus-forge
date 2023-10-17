from kgforge.core.configs.model_config import ModelConfig, ModelContextConfig
from kgforge.core.configs.store_config import StoreConfig

import pytest

@pytest.fixture
def store_config() -> StoreConfig:
    return StoreConfig(bucket="bbp/atlas")


@pytest.fixture
def model_config(store_config) -> ModelConfig:
    return ModelConfig(
        source=store_config, origin="store", context=ModelContextConfig(iri="", source=None)
    )
