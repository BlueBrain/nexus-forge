from typing import Dict, Optional, Union

from kgforge.core import Resource
from kgforge.core.commons.typing import DirPath, FilePath, Hjson, URL
from kgforge.core.storing import Store
from kgforge.core.transforming import Mapping
from kgforge.specializations.mappers import DictionaryMapper


# FIXME FIXME FIXME

class OntologiesHandler:

    def __init__(self, ontologies: Union[DirPath, URL, Store], terms_mapping: Union[Hjson, FilePath, URL]) -> None:
        # Ontologies could be loaded from a directory, an URL, or the store.
        print("FIXME Should implement the loading of the ontologies.")
        print("DEMO - OntologiesHandler")
        self.ontologies = {
            "sex": {
                "male": "http://purl.obolibrary.org/obo/PATO_0000384",
                "female": "http://purl.obolibrary.org/obo/PATO_0000383",
            },
            "species": {
                "Mus musculus": "https://www.ncbi.nlm.nih.gov/taxonomy/10090",
                "Homo sapiens": "http://purl.obolibrary.org/obo/NCBITaxon_9606",
            },
            "brain region": {
                "layer 1": "http://purl.obolibrary.org/obo/UBERON_0005390",
                "layer 2": "http://purl.obolibrary.org/obo/UBERON_0005391",
                "layer 3": "http://purl.obolibrary.org/obo/UBERON_0005392",
                "layer 4": "http://purl.obolibrary.org/obo/UBERON_0005393",
                "layer 5": "http://purl.obolibrary.org/obo/UBERON_0005394",
                "layer 6": "http://purl.obolibrary.org/obo/UBERON_0005395",
            }
        }
        # Ontology terms mapping could be loaded from a Hjson, a file, or an URL.
        print("FIXME Should implement the loading from a file and an URL.")
        self.terms_mapping = Mapping(terms_mapping)

    def resolve(self, type: str, label: str, hint: Optional[str] = None) -> Resource:
        # FIXME
        ontology = self.ontologies[type]
        resolver = OntologyResolver(ontology)
        resolved = resolver.resolve(label, hint)
        return DictionaryMapper(None).map(resolved, self.terms_mapping)


# FIXME Interface / Specialization
class OntologyResolver:

    def __init__(self, ontology) -> None:
        print("DEMO - OntologyResolver")
        self.loaded = ontology

    def resolve(self, label: str, hint: Optional[str] = None) -> Dict:
        print("DEMO - OntologyResolver.resolve()")
        return {
            "id": self.loaded.get(label.lower(), self.loaded[f"{hint} {label.lower()}"]),
            "label": label,
        }
