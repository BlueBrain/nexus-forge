from kgforge.core.commons.typing import Hjson, ManagedData
from kgforge.core.modeling.model import Model


class Neuroshapes(Model):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def template(self, type: str, only_required: bool = False) -> Hjson:
        print("FIXME - Neuroshapes.template()")
        return """
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
            # ...
        """

    def validate_one(self, data: ManagedData) -> bool:
        print("FIXME - Neuroshapes.validate_one()")
        return True
