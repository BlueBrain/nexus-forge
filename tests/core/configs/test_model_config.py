import copy
from typing import Dict

import pytest

from kgforge.core.configs.model_config import ModelConfig, ModelContextConfig
from kgforge.core.configs.store_config import StoreConfig


@pytest.fixture
def model_config(store_config) -> ModelConfig:
    return ModelConfig(
        source="store_1", origin="store", context=ModelContextConfig(iri="", source=None)
    )


@pytest.fixture
def basic_model_context_config() -> ModelContextConfig:
    return ModelContextConfig(iri="", source=None)


@pytest.fixture
def model_config_store_before_merge(basic_model_context_config) -> Dict:
    return dict(
        source="store_1", origin="store", context={"iri": ""}
    )


@pytest.fixture
def model_config_store_after_merge(store_config, basic_model_context_config) -> ModelConfig:
    store_config_edit = copy.deepcopy(store_config)
    store_config_edit.searchendpoints["sparql"]["endpoint"] = "other"

    return ModelConfig(
        source=store_config_edit, origin="store", context=basic_model_context_config
    )


@pytest.fixture
def store_dict(store_config) -> Dict[str, StoreConfig]:
    return {
        "store_1": store_config
    }


def test_model_config_merge_context_store_different(model_config, store_dict):
    # given a context inside a model config using a store,
    # if store information is found within the context, and it's different from the model's
    # store configuration, then it should have its own store configuration

    model_config2 = ModelConfig(context={"bucket": "bbp/else"})

    expected_model_context_store_config = copy.deepcopy(store_dict["store_1"])
    expected_model_context_store_config.bucket = "bbp/else"

    computed_model_config: ModelConfig = ModelConfig.merge_config(
        model_config2, model_config, store_configurations=store_dict
    )

    model_context_store_config = computed_model_config.context.source

    assert model_context_store_config == expected_model_context_store_config


def test_model_config_merge_context_store_same(model_config, store_dict):
    # given a context inside a model config using a store,
    # if store information is found within the context, and it's the same as the model's
    # store configuration, then it shouldn't have its own store configuration
    model_config2 = ModelConfig(context={"bucket": "bbp/atlas", "iri": "some_iri"})
    expected_model_context_store_config = None

    computed_model_config: ModelConfig = ModelConfig.merge_config(
        model_config2, model_config, store_configurations=store_dict
    )

    model_store_config = computed_model_config.source
    model_context_store_config = computed_model_config.context.source

    assert model_context_store_config == expected_model_context_store_config


def test_model_config_merge_context_store_nothing(model_config, store_dict):
    # given a context inside a model config using a store,
    # if no store information is found within the context,
    # then it shouldn't have its own store configuration

    model_config2 = ModelConfig(context={"iri": "some_iri"})
    expected_model_context_store_config = None

    computed_model_config: ModelConfig = ModelConfig.merge_config(
        model_config2, model_config, store_configurations=store_dict
    )

    model_context_store_config = computed_model_config.context.source

    assert model_context_store_config == expected_model_context_store_config


def test_model_config_merge_context_store_nothing_obj(model_config, store_dict):
    # given a context inside a model config using a store,
    # if no store information is found within the context,
    # then it shouldn't have its own store configuration

    model_config2 = ModelConfig(context=ModelContextConfig(iri="some_iri"))

    computed_model_config: ModelConfig = ModelConfig.merge_config(
        model_config2, model_config, store_configurations=store_dict
    )

    expected_model_context_store_config = None
    computed_model_context_store_config = computed_model_config.context.source

    assert computed_model_context_store_config == expected_model_context_store_config


def test_merge_config(
        model_config_store_before_merge, model_config_store_after_merge,
        store_dict
):
    attempt_merge = ModelConfig.merge_config(
        configuration_1=ModelConfig(
            source=dict(id="store_1", searchendpoints={"sparql": {"endpoint": "other"}})
        ),
        configuration_2=model_config_store_before_merge,
        store_configurations=store_dict
    )

    assert model_config_store_after_merge == attempt_merge
