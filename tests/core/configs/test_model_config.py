from typing import Dict

import pytest

from kgforge.core.configs.model_config import ModelConfig
from kgforge.core.configs.store_config import StoreConfig


@pytest.mark.parametrize("model_config_str, context_dict, expected_model_context_config", [
    pytest.param(
        "model_config", {}, None, id="empty-none"
    ),
    pytest.param(
        "model_config",
        {"bucket": "bbp/inference-rules"},
        StoreConfig(bucket="bbp/inference-rules"),
        id="non-empty-non-equal",
    ),
    pytest.param(
        "model_config",
        {"bucket": "bbp/atlas"},
        None,
        id="non-empty-equal",
    )
])
def test_model_config_build_store_config_for_model_context(
        model_config_str: str, context_dict: Dict, expected_model_context_config: StoreConfig,
        request
):

    model_config = request.getfixturevalue(model_config_str)

    computed_model_context_store_config: StoreConfig = ModelConfig.\
        build_store_config_for_model_context(
            model_config.source, context_dict
        )

    assert computed_model_context_store_config == expected_model_context_config

