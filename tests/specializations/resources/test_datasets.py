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

# Placeholder for the generic parameterizable test suite for resources.
from typing import List

from kgforge.core import KnowledgeGraphForge, Resource
from kgforge.specializations.resources import Dataset


def test_from_resource(config, person, organization, store_metadata_value):
    forge = KnowledgeGraphForge(config)
    data = {
        'id': 'c51f4e4e-2b30-41f4-8f7c-aced85632b03',
        'type': ['Person', 'Agent'],
        'name': 'Jami Booth'
    }
    assert isinstance(person, Resource)
    dataset = Dataset.from_resource(forge, person)
    assert isinstance(dataset, Dataset)
    assert forge.as_json(dataset) == forge.as_json(person)
    assert forge.as_json(dataset) == data
    assert dataset._store_metadata is None

    person_with_store_metadata = Resource(**forge.as_json(person))
    person_with_store_metadata._store_metadata = store_metadata_value
    dataset = Dataset.from_resource(forge, person_with_store_metadata, store_metadata=True)
    assert isinstance(dataset, Dataset)
    person_with_store_metadata_json = forge.as_json(person_with_store_metadata)
    assert forge.as_json(dataset) == person_with_store_metadata_json
    assert forge.as_json(dataset) == data
    assert dataset._store_metadata == person_with_store_metadata._store_metadata
    assert forge.as_json(dataset, store_metadata=False) != forge.as_json(person_with_store_metadata, store_metadata=True)
    assert forge.as_json(dataset, store_metadata=True) == forge.as_json(person_with_store_metadata, store_metadata=True)

    assert isinstance(organization, Resource)
    dataset = Dataset.from_resource(forge, [person, organization])
    assert isinstance(dataset, List)
    assert len(dataset) == 2