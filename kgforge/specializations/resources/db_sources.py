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
import json
from pathlib import Path
from typing import Callable, Optional, Union, Dict, List

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping


class DatabaseSource(Resource):

    def __init__(self, type: str = "Database", **properties) -> None:
        """
        The properties defining the Databasesource in YAML are:

           name: <the name of the database>
           type: Database
           origin: <'directory', 'url', or 'store'>
           source: <a directory path, an URL, or the class name of a Store>
           bucket: <when 'origin' is 'store', a Store bucket>
           endpoint: <when 'origin' is 'store', a Store endpoint>
           token: <when 'origin' is 'store', a Store token
           definition:
             origin: <'directory', 'url', or 'store'>
             bucket: <when 'origin' is 'store', a Store bucket>
             endpoint: <when 'origin' is 'store', a Store endpoint>
             token: <when 'origin' is 'store', a Store token, default to Model:token>
             iri: <the IRI of the origin>
        """
        super().__init__(**properties)
        self.type: str = type
    
    def _sources(self) -> List[str]:
        dirpath = Path(self.source, "mappings")
        return [x.stem for x in dirpath.iterdir() if x.is_dir()]

    def _mappings(self, source: str) -> Dict[str, List[str]]:
        dirpath = Path(self.source, "mappings", source)
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        else:
            raise ValueError("unrecognized source")
        return mappings

    def mapping(self, entity: str, source: str, type: Callable) -> Mapping:
        filename = f"{entity}.hjson"
        filepath = Path(self.source, "mappings", source, type.__name__, filename)
        if filepath.is_file():
            return type.load(filepath)
        else:
            raise ValueError("unrecognized entity type or source")
    