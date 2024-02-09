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

from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import numpy as np
from pandas import DataFrame, Series

from kgforge.core.resource import Resource
from kgforge.core.commons.context import Context
from kgforge.core.conversions.json import as_json, from_json


def as_dataframe(data: Union[Resource, List[Resource]], na: Union[Any, List[Any]], nesting: str, expanded: bool,
                 store_metadata: bool, model_context: Optional[Context],
                 metadata_context: Optional[Context], context_resolver: Optional[Callable]) -> DataFrame:
    dicts = as_json(data, expanded, store_metadata, model_context=model_context,
                    metadata_context=metadata_context, context_resolver=context_resolver)
    # NB: Do not use json_normalize(). It does not respect how the dictionaries are ordered.
    flattened = (flatten(x, nesting) for x in dicts) if isinstance(dicts, list) else [flatten(dicts, nesting)]
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
    """


    Parameters
    ----------
    items : List[Tuple[str, Any]]
        at the beginning (first call in the recursion cycle) it is obtain within _from_dataframe as a list, one per row,
        of tuples where the first item is the column name and the second is the value
    sep : str
        the separator. Usually '.'

    Raises
    ------
    ValueError
        One cannot provide both 'property.subproperty1' and 'property'. In such case, a ValueError is raised

    Returns
    -------
    Dict
        a deflattened (nested) dictionary of {columnName: value}.
        Deflatten means that the separator implies nesting of the dictionary.

    """
    d = {}  # dictionary that will be returned
    split = []  # those we have already split (we need to keep track)
    for n1, t1_ in enumerate(items):
        if n1 in split:  # already done, continue
            continue
        k1, v1 = t1_  # all tuples refer to a key-value pair in the DataFrame row
        if isinstance(k1, str) and sep in k1:  # avoid issue if int or other class
            pre, _ = k1.split(sep, maxsplit=1)  # getting prefix ('agent.type' => 'agent')
            if pre in d:  # we already have d[pre] from the else statement, i.e. it appeared without sep!
                raise ValueError(f'Mix of {pre} and {pre}{sep} (e.g. {k1}). Cannot be processed!')
                # e.g. both d['agent'] = 'NicoRicardi' and d['agent.name'] = 'NicoRicardi'
            pitems = []  # any of type {pre}{sep}{depth2}{sep}{depth3} => {depth2}{sep}{depth3}
            for n2, t2_ in enumerate(items):
                k2, v2 = t2_
                if isinstance(k2, str) and k2.startswith(f'{pre}{sep}'):
                    _, post = k2.split(sep, maxsplit=1)  # _ ought to be == pre, but we care mainly about what comes after {pre}{sep}
                    pitems.append((post, v2))
                    split.append(n2)  # we do not need to split this item anymore in this specific recursive call
            d[pre] = deflatten(pitems, sep)  # these items get flattened further in case there is a deeper nesting
        else:
            if k1 in d:  # this key has already been added by the if statement(i.e. from splitting a longer key)
                raise ValueError(f'Mix of {pre} and {pre}{sep} (e.g. {k1}). Cannot be processed!')
                # e.g. both d['agent'] = 'NicoRicardi' and d['agent.name'] = 'NicoRicardi'
            d[k1] = v1  # not nested key-value pair, we just assign
    return d  # all recursive calls are done, i.e. no nesting left, we can return
