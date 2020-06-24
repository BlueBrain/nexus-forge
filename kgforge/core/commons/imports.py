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

import re
from importlib import import_module
from typing import Callable

from kgforge.core.commons.exceptions import ConfigurationError


def import_class(configuration: str, forge_module_name: str) -> Callable:
    # Example use:
    #   - import_class("DemoModel", "models")
    #   - import_class("CustomModel from package.models", "models")
    #   - import_class("CustomModel from package.models.custom_model", "models")
    archetype = forge_module_name[:-1].capitalize()
    matched = re.match("^([A-Za-z]+)(?: from ([a-z_.]+))?$", configuration)
    if matched:
        try:
            forge_module_import = f"kgforge.specializations.{forge_module_name}"
            class_name, module_import = matched.groups(default=forge_module_import)
            module = import_module(module_import)
            return getattr(module, class_name)
        except ModuleNotFoundError:
            raise ConfigurationError(f"{archetype} module not found for '{configuration}'")
        except AttributeError:
            raise ConfigurationError(f"{archetype} class not found for '{configuration}'")
    else:
        raise ConfigurationError(f"incorrect {archetype} configuration for '{configuration}'")
