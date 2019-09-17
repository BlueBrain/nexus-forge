from itertools import groupby
from typing import List

from kgforge.core import Resource


# FIXME FIXME FIXME

# FIXME Use ResourceMapper instead.
# FIXME Case where path goes through a list.
def _reshape(resource: Resource, keep: List[str]) -> Resource:
    def sorting(x): return x[0]
    splitted = (x.split(".", maxsplit=1) for x in keep)
    groups = (list(g) for _, g in groupby(sorted(splitted, key=sorting), key=sorting))
    new = Resource()
    for x in groups:
        if len(x) > 1:
            attribute = x[0][0]
            paths = list(y[1] for y in x)
            _reshape(getattr(resource, attribute), paths)
        else:
            attribute = x[0][0]
            setattr(new, attribute, getattr(resource, attribute))
    return new
