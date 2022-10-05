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
import copy
from typing import Callable, Optional, Union, Dict, List

from kgforge.core import Resource
from kgforge.core.archetypes import Mapping, Store, Model
from kgforge.core.commons.execution import not_supported
from kgforge.core.commons.dictionaries import with_defaults
from kgforge.core.commons.imports import import_class

# Get local paths
pathparts = list(Path(__file__).resolve().parts)
KGFORGE_PATH = os.path.join(*pathparts[:-4])
DBS_PATH = Path(KGFORGE_PATH, "examples", "database_sources")

class DatabaseSource(Resource):
    """A high-level class for Database-related Resources."""
    

    _DBDIR = Path
    _REQUIRED = ("name", "store", "model")
    _RESERVED = {"_forge", "_from_forge", "_check_properties", "_save_config", "_dirpath",
                 "health", "_mappings", "mappings", "mapping", "dump_config", "_model", "._store"} | Resource._RESERVED

    def __init__(self, forge: Optional["KnowledgeGraphForge"], type: str = "Database",
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
           model:
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
        

        store_config = properties.pop('store')

        # Model
        model_config = properties.pop("model")
        # Assume that the model is a store
        # TODO: get configuration from forge._store when using BlueBrainNexus
        if model_config["origin"] == "store":
            with_defaults(
                model_config,
                store_config,
                "source",
                "name",
                ["endpoint", "token", "bucket", "vocabulary"],
            )
        model_name = model_config.pop("name")
        model = import_class(model_name, "models")
        self._model: Model = model(**model_config)

        # Store.
        store_name = store_config.pop("name")
        store = import_class(store_name, "stores")
        self._store: Store = store(**store_config)
        store_config.update(name=store_name)

        self._from_forge = from_forge
        self._dirpath = os.path.join(DBS_PATH, self.name)
        if self._from_forge is False:
            # Save in directory and add it to forge instance
            self._save_config()
        else:
            if not Path(self._dirpath).is_dir():
                raise ValueError(f"Database directory for {self.name} was not found.\
                                   To create a new database use from_forge=False")
    
    def _check_properties(self, **info):
        properties = info.keys()
        for r in self._REQUIRED:
            if r not in properties:
                raise ValueError(f'Missing {r} from the properties to define the DatabaseResource')

    def _save_config(self) -> None:
        """Save database information inside the kgforge database folder."""
        # Make mappings directory
        Path(self._dirpath).mkdir(parents=True, exist_ok=True)
        Path(self._dirpath, 'mappings').mkdir(parents=True, exist_ok=True)
        # Add the source to forge
        self._forge.add_db_source(self)
    
    def datatypes(self):
        # TODO: add other datatypes used, for instance, inside the mappings
        return self.mappings(pretty=False).keys()

    def _model(self) -> None:
        not_supported()

    def _mappings(self) -> Dict[str, List[str]]:
        dirpath = Path(self._dirpath, "mappings")
        mappings = {}
        if dirpath.is_dir():
            for x in dirpath.glob("*/*.hjson"):
                mappings.setdefault(x.stem, []).append(x.parent.name)
        else:
            raise ValueError("unrecognized source")
        return mappings

    def mappings(self, pretty: bool) -> Optional[Dict[str, List[str]]]:
        mappings = {k: sorted(v) for k, v in
                    sorted(self._mappings().items(), key=lambda kv: kv[0])}
        if pretty:
            print("Managed mappings for the data source per entity type and mapping type:")
            for k, v in mappings.items():
                print(*[f"   - {k}:", *v], sep="\n        * ")
        else:
            return mappings

    def mapping(self, entity: str, type: Callable) -> Mapping:
        filename = f"{entity}.hjson"
        filepath = Path(self._dirpath, "mappings", type.__name__, filename)
        if filepath.is_file():
            return type.load(filepath)
        else:
            raise ValueError("unrecognized entity type or source")

    def dump_config(self) -> None:
        filename = "config.json"
        filepath = Path(self._dirpath, filename)
        with open(filepath, 'w') as mfile:
            return mfile.write(json.dumps(self._forge.as_json(self), indent=4))
    
    def health(self):
        not_supported()