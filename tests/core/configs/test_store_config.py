import copy
from typing import Dict
import pytest

from kgforge.core.configs.store_config import StoreConfig


def test_merge_config_attribute_flat(store_config):
    store_config_after_merge = copy.deepcopy(store_config)
    store_config_after_merge.bucket = "bbp/other"

    attempt_merge = StoreConfig.merge_config(
        configuration_1=StoreConfig(bucket="bbp/other"),
        configuration_2=store_config,
    )

    attempt_merge2 = StoreConfig.merge_config(
        configuration_1=dict(bucket="bbp/other"),
        configuration_2=store_config,
    )

    assert store_config_after_merge == attempt_merge
    assert store_config_after_merge == attempt_merge2


def test_merge_config_attribute_dict(store_config):
    store_config_after_merge = copy.deepcopy(store_config)
    store_config_after_merge.searchendpoints["sparql"]["endpoint"] = "other"
    # elastic should not be overwritten

    attempt_merge = StoreConfig.merge_config(
        configuration_1=StoreConfig(searchendpoints={"sparql": {"endpoint": "other"}}),
        configuration_2=store_config,
    )

    attempt_merge2 = StoreConfig.merge_config(
        configuration_1=dict(searchendpoints={"sparql": {"endpoint": "other"}}),
        configuration_2=store_config,
    )

    assert store_config_after_merge == attempt_merge
    assert store_config_after_merge == attempt_merge2
