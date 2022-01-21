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
from kgforge.core.commons.execution import catch, not_supported
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
    def add_contribution(self, resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None:
        # resource: Union[str, Resource].
        """Add information on the contribution of an agent during the generation of the dataset."""

        keep = ["id", "type", "_store_metadata"]
        contribution = self._add_prov_property(resource, "Contribution", "agent", "Agent", keep, versioned,
                                             **kwargs)
        _set(self, "contribution", contribution)

    @catch
    def add_generation(self, resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None:
        """Add information about the activity that generated the dataset."""

        keep = ["id", "type", "_store_metadata"]
        generation = self._add_prov_property(resource, "Generation", "activity", "Activity", keep, versioned,
                                             **kwargs)
        _set(self, "generation", generation)

    @catch
    def add_derivation(self, resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None:
        """Add information about the resources from which the dataset was derived."""

        keep = ["id", "type", "name", "_store_metadata"]
        derivation = self._add_prov_property(resource, "Derivation", "entity", "Entity", keep, versioned,
                                             **kwargs)
        _set(self, "derivation", derivation)

    @catch
    def add_invalidation(self, resource: Union[str, Resource], versioned: bool = True, **kwargs) -> None:
        """Add information about the invalidation of the dataset."""

        keep = ["id", "type", "_store_metadata"]
        invalidation = self._add_prov_property(resource,"Invalidation","activity","Activity",keep,versioned, **kwargs)
        _set(self, "invalidation", invalidation)

    def _add_prov_property(self,resource, prov_type, reference_property, reference_type, keep, versioned, **kwargs):

        if versioned and isinstance(resource, str):
            not_supported((f"resource:str when versioned is {versioned}. Set 'versioned' to False when referencing a str.", True))
        if isinstance(resource, str):
            reference = Resource(type=reference_type, id=resource)
        elif isinstance(resource, Resource):
            try:
                reference = self._forge.reshape(resource, keep, versioned)
            except AttributeError as ae:
                if '_rev' in str(ae) and versioned:
                    raise ValueError(f"Missing resource revision value to build a versioned ({versioned}) reference. "
                                     f"Provide a revision number to the resource (by registering it for example) or set 'versioned' argument to False if no versioned reference is needed.")
                else:
                    raise ae

        result = Resource(type=prov_type, **kwargs)
        result.__setattr__(reference_property,reference)
        return result

    @catch
    def add_files(self, path: str, content_type: str = None) -> None:
        # path: DirPath.
        """Add (different) files as parts of the dataset."""
        action = self._forge.attach(path, content_type)
        distribution = Resource(distribution=action)
        _set(self, "hasPart", distribution)

    @catch
    def download(self, path: str, source: str = "distributions", overwrite: bool = False, cross_bucket: bool = False) -> None:
        # path: DirPath.
        """Download the distributions of the dataset or the files part of the dataset."""
        if source == "distributions":
            follow = "distribution.contentUrl"
        elif source == "parts":
            follow = "hasPart.distribution.contentUrl"
        else:
            raise ValueError("unrecognized source")
        self._forge.download(self, follow, path, overwrite, cross_bucket)

    @classmethod
    def from_resource(cls, forge: KnowledgeGraphForge, data: Union[Resource, List[Resource]],
                      store_metadata: bool = False):
        def _(d):
            resource_json = forge.as_json(d)
            dataset = cls(forge, **resource_json)
            if store_metadata:
                dataset._store_metadata = d._store_metadata
            return dataset
        return [_(d) for d in data] if isinstance(data, List) else _(data)


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
