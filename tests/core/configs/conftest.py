from typing import Dict

from kgforge.core.configs.model_config import ModelConfig, ModelContextConfig
from kgforge.core.configs.store_config import StoreConfig

import pytest


@pytest.fixture
def store_config() -> StoreConfig:
    return StoreConfig(
        bucket="bbp/atlas",
        name="BlueBrainNexus",
        endpoint="https://bbp.epfl.ch/nexus/v1",
        searchendpoints=dict(
            sparql={
                "endpoint": "https://bluebrain.github.io/nexus/vocabulary/defaultSparqlIndex"
            },
            elastic={
                "endpoint": "https://bbp.epfl.ch/neurosciencegraph/data/views/aggreg-es/dataset",
                "mapping": "https://bbp.epfl.ch/neurosciencegraph/data/views/es/dataset",
                "default_str_keyword_field": "keyword"
            }
        ),
        vocabulary=dict(
            metadata=dict(
                iri="https://bluebrain.github.io/nexus/contexts/metadata.json",
                local_iri="https://bluebrainnexus.io/contexts/metadata.json"
            ),
            namespace="https://bluebrain.github.io/nexus/vocabulary/",
            deprecated_property="https://bluebrain.github.io/nexus/vocabulary/deprecated",
            project_property="https://bluebrain.github.io/nexus/vocabulary/project"

        ),
        max_connection=5,
        versioned_id_template="{x.id}?rev={x._store_metadata._rev}",
        file_resource_mapping="https://raw.githubusercontent.com/BlueBrain/nexus-forge/master/examples/configurations/nexus-store/file-to-resource-mapping.hjson"
    )

