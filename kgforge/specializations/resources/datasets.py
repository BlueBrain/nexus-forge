from typing import List, Optional, Union

from kgforge.core.commons.actions import LazyAction
from kgforge.core.commons.typing import DirPath, IRI, ManagedData, as_list
from kgforge.core.forge import KnowledgeGraphForge
from kgforge.core.resources import Resource, Resources


class Dataset(Resource):
    """An opinionated way of dealing with collections of Resources."""

    _RESERVED = {"_forge", "parts", "with_parts", "files", "with_files", "contributors",
                 "with_contributors", "derivations", "with_derivations"} | Resource._RESERVED

    def __init__(self, forge: KnowledgeGraphForge, type: str = "Dataset", **properties) -> None:
        super().__init__(**properties)
        self._forge = forge
        self.type = type

    def parts(self) -> Optional[Resources]:
        """Returns resources part of the dataset (schema:hasPart)."""
        return getattr(self, "hasPart", None)

    def with_parts(self, resources: ManagedData, versioned: bool = True) -> None:
        """Set resources part of the dataset (schema:hasPart)."""
        keep = ["type", "id", "name", "distribution.contentUrl"]
        self.hasPart = self._forge.transforming.reshape(resources, keep, versioned)

    def files(self) -> Optional["DatasetFiles"]:
        """Returns files part of the dataset (schema:distribution) in an handler."""
        try:
            distribution = Resources(x.distribution for x in as_list(self.hasPart))
        except AttributeError:
            hasPart = self.parts()
            return hasPart if isinstance(hasPart, LazyAction) else None
        else:
            return DatasetFiles(self._forge, distribution)

    def with_files(self, path: DirPath) -> None:
        """Set files part of the dataset (schema:distribution)."""
        self.hasPart = self._forge.files.as_resource(path)

    def contributors(self) -> Optional[Resources]:
        return getattr(self, "contribution", None)

    def with_contributors(self, agents: Union[IRI, List[IRI]]) -> None:
        # FIXME Check how to best include the optional resources (Plan, Role).
        self.contribution = [Resource(type="Contribution", agent=x) for x in as_list(agents)]

    def derivations(self) -> Optional[Resources]:
        return getattr(self, "derivation", None)

    def with_derivations(self, resources: Union[Resource, Resources], versioned: bool = True) -> None:
        # FIXME Check how to best include the optional resources (Activity, Usage).
        keep = ["type", "id"]
        entities = self._forge.transforming.reshape(resources, keep, versioned)
        self.derivation = [Resource(type="Derivation", entity=x) for x in entities]

    # FIXME Implement methods for 'generation' and 'invalidation' as for derivation.


class DatasetFiles(Resources):

    # Should not be exposed to the users (i.e. do not import in the package __init__).

    def __init__(self, forge: KnowledgeGraphForge, distribution: ManagedData) -> None:
        super().__init__(distribution)
        self.forge = forge

    def download(self, path: DirPath) -> None:
        self.forge.querying.download(self, "contentUrl", path)
