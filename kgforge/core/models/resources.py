from typing import Dict, Iterator, Sequence, Union

import hjson


class Resource:
    RESERVED = ["_forge"]

    def __init__(self, forge, **properties) -> None:
        self._forge = forge
        for k, v in properties.items():
            if k in self.RESERVED:
                raise NotImplementedError
            setattr(self, k, v)

    # FIXME Implement __eq__.

    def __repr__(self) -> str:
        type_ = getattr(self, "type", None)
        id_ = getattr(self, "id", None)
        return f"Resource(type={type_}, id={id_})"

    def __str__(self) -> str:
        serialized = self._to_dict()
        return hjson.dumps(serialized, indent=4)

    def _to_dict(self) -> Dict:
        return {k: v._to_dict() if isinstance(v, Resource) else v
                for k, v in self.__dict__.items() if k not in self.RESERVED}


# FIXME Check if inheriting directly from 'list' is a good idea.
class Resources(list):

    def __init__(self, resources: Union[Sequence[Resource], Iterator[Resource]]) -> None:
        super().__init__(resources)
