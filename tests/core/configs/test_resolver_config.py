import copy
from typing import Dict

import pytest

from kgforge.core.configs.resolver_config import ResolverConfig
from kgforge.core.configs.store_config import StoreConfig


@pytest.fixture
def resolver_config(store_config) -> ResolverConfig:
    return ResolverConfig(source="store_1", origin="store")


@pytest.fixture
def store_dict(store_config) -> Dict[str, StoreConfig]:
    return {
        "store_1": store_config
    }


def test_merge_config(store_dict, resolver_config):
    resolver_config_store_before_merge = dict(
        source="store_1", origin="store", context={"iri": ""}
    )

    resolver_config_store_after_merge = copy.deepcopy(resolver_config)
    resolver_config_store_after_merge.source = copy.deepcopy(store_dict["store_1"])
    resolver_config_store_after_merge.source.searchendpoints["sparql"]["endpoint"] = "other"

    attempt_merge = ResolverConfig.merge_config(
        configuration_1=ResolverConfig(
            source=dict(id="store_1", searchendpoints={"sparql": {"endpoint": "other"}})
        ),
        configuration_2=resolver_config_store_before_merge,
        store_configurations=store_dict
    )

    assert resolver_config_store_after_merge == attempt_merge
