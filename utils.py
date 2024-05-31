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

from urllib.parse import quote_plus
import os

from kgforge.specializations.stores.nexus.https_helpers import project_fetch

TOKEN = ""
base_prod_v1 = "https://bbp.epfl.ch/nexus/v1"


"""
This is a temporary uri rewriter to cope with the fact that some BlueBrainNexus users might have copied and stored outside BlueBrainNexus some _self urls of resources
or files that was expecting a given base as per the project config. Now that the project config changed with a new base, those urls are no longer working.
This method is going back in history to find the previous base and apply it to generate a resolvable url.
We expect the user to replace the previous _self url with this newly generated one so that this method is not needed anymore.

Call example: 
org     = "bbp" 
project = "mmb-point-neuron-framework-model"
uri = "https://bbp.epfl.ch/nexus/v1/files/bbp/mmb-point-neuron-framework-model/79b51b75-81e2-4b2f-98fc-666130512cea"

uri_formatter_using_previous_project_config(nxs,uri,org, project)

This returns for example:
https://bbp.epfl.ch/nexus/v1/files/bbp/mmb-point-neuron-framework-model/https%3A%2F%2Fbbp.epfl.ch%2Fneurosciencegraph%2Fdata%2F79b51b75-81e2-4b2f-98fc-666130512cea
"""


def uri_formatter_using_previous_project_config(nxs, uri, org, project):
    # Retrieve current project description
    current_project_description = nxs.projects.fetch(org, project)
    current_project_description = dict(current_project_description)
    # current_base = current_project_description["base"]
    # current_vocab = current_project_description["vocab"]
    current_project_revision = current_project_description['_rev']

    if current_project_revision <= 1:
        raise Exception(f"The targeted project {org}/{project} does not have a previous revision. It's config was never changed.")

    # Retrieve previous project description
    previous_project_revision = current_project_revision - 1
    previous_project_description = project_fetch(endpoint=base_prod_v1, token=TOKEN, org_label=org, project_label=project, rev=previous_project_revision)
    previous_project_description = dict(previous_project_description)
    previous_base = previous_project_description["base"]
    # previous_vocab = previous_project_description["vocab"]
    previous_project_revision = previous_project_description['_rev']

    uri_parts = uri.split("/")
    uri_last_path = uri_parts[-1]
    uri_last_path = uri_last_path.split("?")  # in case ? params are in the url
    if len(uri_last_path) > 1:
        uri_last_path = uri_last_path[-2]
    else:
        uri_last_path = uri_last_path[-1]
    expanded_uri_last_path = previous_base + uri_last_path
    formatted_uri_parts = uri.replace(uri_last_path, quote_plus(expanded_uri_last_path))
    formatter_uri = "".join(formatted_uri_parts)
    return formatter_uri


def full_path_relative_to_root(path: str):
    """
   Provided a path relative to the root of the repository, it is transformed into an absolute path
   so that it will be independent of what the working directory is
   """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
