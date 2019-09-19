from typing import Dict, List

from kgforge.core import Resource
from kgforge.core.commons.typing import Hjson
from kgforge.core.modeling.model import Model


class MissingProperty(ValidationError):

    pass


class DemoModel(Model):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("DEMO - DemoModel")
        # DEMO Simplified case where the model is expressed already in the format of the templates.
        self.schemas = {
            "Subject": SUBJECT,
            "PatchedCell": PATCHED_CELL,
            "NeuronMorphology": NEURONMORPHOLOGY,
        }

    def prefixes(self) -> Dict[str, str]:
        print("DEMO - DemoModel.prefixes()")
        return {
            "schema": "http://schema.org/",
            "prov": "http://www.w3.org/ns/prov#",
        }

    def types(self) -> List[str]:
        print("DEMO - DemoModel.types()")
        return list(self.schemas.keys())

    def template(self, type: str, only_required: bool = False) -> Hjson:
        print("DEMO - DemoModel.template()")
        if only_required:
            not_supported("only_required", "DemoModel")
        return self.schemas[type]

    def _validate_one(self, resource: Resource) -> None:
        print("DEMO - DemoModel.validate_one()")
        if not hasattr(resource, "name"):
            raise MissingProperty("name")


SUBJECT = """
            type: Subject
            id: null
            identifier: null
            name: null
            sex:
            {
                id: null
                label: null
            }
            species:
            {
                id: null
                label: null
            }
        """

PATCHED_CELL = """
    type: PatchedCell
    id: null
    brainLocation:
    {
        type: BrainLocation
        brainRegion:
        {
            id: null
            label: null
        }
    }
    contribution:
    {
        type: Contribution
        agent:
        {
            type: Agent
            id: null
        }
    }
    derivation:
    {
        type: Derivation
        entity:
        {
            type: Entity
            id: null
        }
    }
    identifier: null
    name: null
"""

NEURONMORPHOLOGY = """
    type: NeuronMorphology
    id: null
    brainLocation:
    {
        type: BrainLocation
        brainRegion:
        {
            id: null
            label: null
        }
        coordinatesInBrainAtlas:
        {
            valueX: null
            valueY: null
            valueZ: null
        }
        layer:
        {
            id: null
            label: null
        }
    }
    contribution:
    {
        type: Contribution
        agent:
        {
            type: Agent
            id: null
        }
    }
    derivation:
    {
        type: Derivation
        entity:
        {
            type: Entity
            id: null
        }
    }
    distribution:
    {
        type: DataDownload
        contentSize:
        {
            value: null
            unitCode: null
        }
        contentUrl:
        {
            id: null
        }
        digest:
        {
            algorithm: null
            value: null
        }
        encodingFormat: null
        name: null
    }
    identifier: null
    name: null
"""
