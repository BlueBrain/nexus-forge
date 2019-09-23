from typing import Iterator, List, Optional, Sequence, Union

from kgforge.core.commons.attributes import check_collisions
from kgforge.core.commons.typing import DirPath, IRI, as_list_if_not
from kgforge.core.resources import Resource, Resources


class Dataset(Resource):

    _RESERVED = {"_forge", "type", "parts", "with_parts", "files", "with_files", "contributors",
                 "with_contributors", "derivations", "with_derivations"}

    def __init__(self, forge, type: str = "Dataset", **properties) -> None:
        super().__init__(**properties)
        check_collisions(self._RESERVED, properties.keys())
        self._forge = forge
        self.type = type

    def parts(self) -> Optional[Resources]:
        """Returns resources part of the dataset (i.e. in schema:hasPart)."""
        return getattr(self, "hasPart", None)

    def with_parts(self, resources: Union[Resource, Resources], versioned: bool = True) -> None:
        """Set resources part of the dataset (i.e. in schema:hasPart)."""
        keep = ["id", "type", "name", "distribution.contentUrl"]
        self.hasPart = self._forge.transforming.reshape(as_list_if_not(resources), keep, versioned)

    def files(self) -> Optional["DatasetFiles"]:
        """Returns files part of the dataset (i.e. in schema:distribution) in an handler."""
        try:
            distribution = self.hasPart.distribution
        except AttributeError:
            return None
        else:
            return DatasetFiles(self._forge, distribution)

    def with_files(self, path: DirPath) -> None:
        """Set files part of the dataset (i.e. in schema:distribution)."""
        self.distribution = self._forge.files.as_resource(path)

    def contributors(self) -> Optional[Resources]:
        return getattr(self, "contribution", None)

    # FIXME Check how to best include the optional resources (Plan, Role).
    def with_contributors(self, agents: Union[IRI, List[IRI]]) -> None:
        self.contribution = [Resource(type="Contribution", agent=x) for x in as_list_if_not(agents)]

    def derivations(self) -> Optional[Resources]:
        return getattr(self, "derivation", None)

    # FIXME Check how to best include the optional resources (Activity, Usage).
    def with_derivations(self, resources: Union[Resource, Resources], versioned: bool = True) -> None:
        keep = ["id", "type"]
        entities = self._forge.transforming.reshape(as_list_if_not(resources), keep, versioned)
        self.derivation = [Resource(type="Derivation", entity=x) for x in entities]

    # FIXME Implement for 'generation' and 'invalidation' properties methods as for derivation.


class DatasetFiles(Resources):

    # Should not be exposed to the users (i.e. do not import in the package __init__).

    def __init__(self, forge, resources: Union[Sequence[Resource], Iterator[Resource]]) -> None:
        super().__init__(resources)
        self.forge = forge

    def download(self, path: DirPath) -> None:
        self.forge.querying.download(self, "contentUrl", path)
