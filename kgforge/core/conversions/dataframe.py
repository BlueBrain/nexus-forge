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

from typing import Any, Dict, Iterator, List, Tuple, Union

import numpy as np
from pandas import DataFrame, Series

from kgforge.core import Resource
from kgforge.core.conversions.json import as_json, from_json


def as_dataframe(data: List[Resource], na: Union[Any, List[Any]], nesting: str, expanded: bool,
                 store_metadata: bool) -> DataFrame:
    dicts = as_json(data, expanded, store_metadata)
    # NB: Do not use json_normalize(). It does not respect how the dictionaries are ordered.
    flattened = (flatten(x, nesting) for x in dicts)
    df = DataFrame(flattened)
    if na is not None:
        df.replace(na, np.nan, inplace=True)
    return df


def flatten(data: Dict, sep: str) -> Dict:
    return dict(_flatten(data, sep, []))


def _flatten(data: Dict, sep: str, path: List[str]) -> Iterator[Tuple[str, Any]]:
    for k, v in data.items():
        p = [*path, k]
        if isinstance(v, Dict):
            yield from _flatten(v, sep, p)
        else:
            yield sep.join(p), v


def from_dataframe(data: DataFrame, na: Union[Any, List[Any]], nesting: str
                   ) -> Union[Resource, List[Resource]]:
    converted = [_from_dataframe(x, na, nesting) for _, x in data.iterrows()]
    if len(converted) == 1:
        converted = converted[0]
    return converted


def _from_dataframe(row: Series, na: Union[Any, List[Any]], nesting: str) -> Resource:
    new_na = row.replace(na, np.nan)
    no_na = new_na.dropna()
    items = list(no_na.items())
    data = deflatten(items, nesting)
    return from_json(data, None)


def deflatten(items: List[Tuple[str, Any]], sep: str) -> Dict:
    d = dict()
    i = 0
    while i < len(items):
        k, v = items[i]
        if sep not in k:
            d[k] = v
            i += 1
        else:
            pk, _, ck = k.partition(sep)
            pitems = list(take_while(items[i:], f"{pk}{sep}"))
            d[pk] = deflatten(pitems, sep)
            i += len(pitems)
    return d


def take_while(items: List[Tuple[str, Any]], start: str) -> Iterator[Tuple[str, Any]]:
    for k, v in items:
        if k.startswith(start):
            yield k.replace(start, "", 1), v
        else:
            break
