# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

from typing import Union

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.typing import DirPath, FilePath, IRI, ManagedData
from kgforge.core.forge import KnowledgeGraphForge
from kgforge.core.resources import Resource, Resources


class Dataset(Resource):
    """An opinionated high-level class based on Resource to handle datasets."""

    _RESERVED = {"_forge", "add_parts", "add_distribution", "add_contribution", "add_generation",
                 "add_derivation", "add_invalidation", "add_files", "download"} | Resource._RESERVED

    def __init__(self, forge: KnowledgeGraphForge, type: str = "Dataset", **properties) -> None:
        super().__init__(**properties)
        self._forge = forge
        self.type = type

    def add_parts(self, resources: Resources, versioned: bool = True) -> None:
        """Make resources part of the dataset."""
        keep = ["id", "type", "name", "distribution.contentUrl"]
        reshaped = self._forge.transforming.reshape(resources, keep, versioned)
        _set(self, "hasPart", reshaped)

    def add_distribution(self, path: FilePath) -> None:
        """Add a downloadable form of the dataset."""
        action = self._forge.files.as_resource(path)
        _set(self, "distribution", action)

    def add_contribution(self, agent: IRI, **kwargs) -> None:
        """Add information on the contribution of an agent during the generation of the dataset."""
        agent = Resource(type="Agent", id=agent)
        resource = Resource(type="Contribution", agent=agent, **kwargs)
        _set(self, "contribution", resource)

    def add_generation(self, **kwargs) -> None:
        """Add information on the activity which has resulted in the generation of the dataset."""
        if not kwargs:
            raise TypeError("at least one argument should be given")
        resource = Resource(type="Generation", **kwargs)
        _set(self, "generation", resource)

    def add_derivation(self, resource: Resource, versioned: bool = True, **kwargs) -> None:
        """Add information on the derivation of an entity resulting in the dataset."""
        keep = ["id", "type", "name"]
        entity = self._forge.transforming.reshape(resource, keep, versioned)
        qualified = Resource(type="Derivation", entity=entity, **kwargs)
        _set(self, "derivation", qualified)

    def add_invalidation(self, **kwargs) -> None:
        """Add information on the invalidation of the dataset."""
        if not kwargs:
            raise TypeError("at least one argument should be given")
        resource = Resource(type="Invalidation", **kwargs)
        _set(self, "invalidation", resource)

    def add_files(self, path: DirPath) -> None:
        """Add (different) files as parts of the dataset."""
        action = self._forge.files.as_resource(path)
        _set(self, "hasPart", action)

    def download(self, source: str, path: DirPath) -> None:
        """Download the distributions of the dataset or the files part of the dataset."""
        if source == "distributions":
            follow = "distribution.contentUrl"
        elif source == "parts":
            follow = "hasPart.distribution.contentUrl"
        else:
            raise ValueError("unrecognized source")
        self._forge.querying.download(self, follow, path)


def _set(dataset: Dataset, attr: str, data: Union[ManagedData, LazyAction]) -> None:
    if hasattr(dataset, attr):
        value = getattr(dataset, attr)
        if isinstance(value, Resources):
            if isinstance(data, Resources):
                value.extend(data)
            else:
                value.append(data)
        else:
            if isinstance(data, Resources):
                new = Resources((value, *data))
            else:
                new = Resources((value, data))
            setattr(dataset, attr, new)
    else:
        setattr(dataset, attr, data)
