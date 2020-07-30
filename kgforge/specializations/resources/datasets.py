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

from typing import List, Union

from kgforge.core import Resource
from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.execution import catch
from kgforge.core.forge import KnowledgeGraphForge


# POLICY _set() should be only called as the last statement to ensure atomicity in case of errors.


class Dataset(Resource):
    """An opinionated high-level class based on Resource to handle datasets."""

    _RESERVED = {"_forge", "add_parts", "add_distribution", "add_contribution", "add_generation",
                 "add_derivation", "add_invalidation", "add_files",
                 "download"} | Resource._RESERVED

    # No catching of exceptions so that no incomplete instance is created if an error occurs.
    # This is a best practice in Python for __init__().
    def __init__(self, forge: KnowledgeGraphForge, type: str = "Dataset", **properties) -> None:
        super().__init__(**properties)
        self._forge: KnowledgeGraphForge = forge
        self.type: str = type

    @catch
    def add_parts(self, resources: List[Resource], versioned: bool = True) -> None:
        """Make resources part of the dataset."""
        keep = ["id", "type", "name", "distribution.contentUrl"]
        parts = self._forge.reshape(resources, keep, versioned)
        _set(self, "hasPart", parts)

    @catch
    def add_distribution(self, path: str, content_type: str = None) -> None:
        # path: FilePath.
        """Add a downloadable form of the dataset."""
        action = self._forge.attach(path, content_type)
        _set(self, "distribution", action)

    @catch
    def add_contribution(self, agent_id: str, **kwargs) -> None:
        # agent: IRI.
        """Add information on the contribution of an agent during the generation of the dataset."""
        agent = Resource(type="Agent", id=agent_id)
        contribution = Resource(type="Contribution", agent=agent, **kwargs)
        _set(self, "contribution", contribution)

    @catch
    def add_generation(self, **kwargs) -> None:
        """Add information on the activity which has resulted in the generation of the dataset."""
        if not kwargs:
            raise TypeError("at least one argument should be given")
        generation = Resource(type="Generation", **kwargs)
        _set(self, "generation", generation)

    @catch
    def add_derivation(self, resource: Resource, versioned: bool = True, **kwargs) -> None:
        """Add information on the derivation of an entity resulting in the dataset."""
        keep = ["id", "type", "name"]
        entity = self._forge.reshape(resource, keep, versioned)
        derivation = Resource(type="Derivation", entity=entity, **kwargs)
        _set(self, "derivation", derivation)

    @catch
    def add_invalidation(self, **kwargs) -> None:
        """Add information on the invalidation of the dataset."""
        if not kwargs:
            raise TypeError("at least one argument should be given")
        invalidation = Resource(type="Invalidation", **kwargs)
        _set(self, "invalidation", invalidation)

    @catch
    def add_files(self, path: str, content_type: str = None) -> None:
        # path: DirPath.
        """Add (different) files as parts of the dataset."""
        action = self._forge.attach(path, content_type)
        distribution = Resource(distribution=action)
        _set(self, "hasPart", distribution)

    @catch
    def download(self, source: str, path: str, overwrite: bool = False) -> None:
        # path: DirPath.
        """Download the distributions of the dataset or the files part of the dataset."""
        if source == "distributions":
            follow = "distribution.contentUrl"
        elif source == "parts":
            follow = "hasPart.distribution.contentUrl"
        else:
            raise ValueError("unrecognized source")
        self._forge.download(self, follow, path, overwrite)


def _set(dataset: Dataset, attr: str, data: Union[Resource, List[Resource], LazyAction]) -> None:
    if hasattr(dataset, attr):
        value = getattr(dataset, attr)
        if isinstance(value, List):
            if isinstance(data, List):
                value.extend(data)
            else:
                value.append(data)
        else:
            if isinstance(data, List):
                new = [value, *data]
            else:
                new = [value, data]
            setattr(dataset, attr, new)
    else:
        setattr(dataset, attr, data)
