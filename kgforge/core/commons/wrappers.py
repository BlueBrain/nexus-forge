from typing import Any, Dict


# FIXME Check if inheriting directly from 'dict' is a good idea.
class AttrsDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def wrap(data: Any) -> "AttrsDict":
        if isinstance(data, Dict):
            return AttrsDict({k: AttrsDict.wrap(v) for k, v in data.items()})
        else:
            return data
