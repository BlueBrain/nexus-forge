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
import os
import json
from pathlib import Path, PurePath
from re import I
from typing import Callable, Optional, Union, Dict, List

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping

# Get local paths
pathparts = list(Path(__file__).resolve().parts)
KGFORGE_PATH = os.path.join(*pathparts[:-4])
DBS_PATH = os.path.join(KGFORGE_PATH, "examples", "database_sources")

class DatabaseSource(Resource):
    """A high-level class for Database-related Resources."""
    

    _DBDIR = Path
    _REQUIRED = ("name", "origin", "source", "definition")
    _RESERVED = {"_forge", "_from_forge", "_check_properties", "_save_config", "_dirpath",
                 "_mappings", "mappings"} | Resource._RESERVED

    def __init__(self, forge: Optional["KnowledgeGRaphForge"], type: str = "Database",
                 from_forge: bool = True, **properties) -> None:
        """
        The properties defining the Databasesource in YAML are:

           name: <the name of the database> - REQUIRED
           type: Database - REQUIRED
           origin: <'directory', 'url', or 'store'> - REQUIRED
           source: <a directory path, an URL, or the class name of a Store> - REQUIRED
           bucket: <when 'origin' is 'store', a Store bucket>
           endpoint: <when 'origin' is 'store', a Store endpoint>
           token: <when 'origin' is 'store', a Store token
           definition: - REQUIRED
             origin: <'directory', 'url', or 'store'>
             bucket: <when 'origin' is 'store', a Store bucket>
             endpoint: <when 'origin' is 'store', a Store endpoint>
             token: <when 'origin' is 'store', a Store token, default to Model:token>
             iri: <the IRI of the origin>
        """
        self._check_properties(**properties)
        super().__init__(**properties)
        self.type: str = type
        self._forge: Optional["KnowledgeGraphForge"] = forge
        self._from_forge = from_forge
        if self._from_forge is False:
            self._save_config()
    
    def _check_properties(self, **info):
        properties = info.keys()
        for r in self._REQUIRED:
            if r not in properties:
                raise ValueError(f'Missing {r} from the properties to define the DatabaseResource')

    def _save_config(self) -> None:
        """Save database information inside the kgforge database folder."""
        self._dirpath = os.path.join(DBS_PATH, self.name)
        Path(self._dirpath).mkdir(parents=True, exist_ok=True)
        # Make mappings directory
        Path(self._dirpath, 'mappings').mkdir(parents=True, exist_ok=True)
        # Add the source to forge
        self._forge.add_db_source(self)
    
    def _mappings(self) -> Dict[str, List[str]]:
        dirpath = Path(self._dirpath, "mappings")
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        else:
            raise ValueError("unrecognized source")
        return mappings

    def mapping(self, entity: str, type: Callable) -> Mapping:
        filename = f"{entity}.hjson"
        filepath = Path(self._dirpath, "mappings", type.__name__, filename)
        print(filepath)
        if filepath.is_file():
            return type.load(filepath)
        else:
            raise ValueError("unrecognized entity type or source")
    