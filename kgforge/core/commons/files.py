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
from builtins import all

from pathlib import Path
import requests
from requests import RequestException
from urllib.parse import urlparse

def load_file_as_byte(source: str):
    # source: Union[str, FilePath, URL].
    filepath = Path(source)
    if filepath.is_file():
        data = filepath.read_bytes()
    else:
        try:
            response = requests.get(source)
            response.raise_for_status()
            data = response.content
        except RequestException as re:
            raise AttributeError(f"Failed to load the configuration from {source}. The provided source is not a valid file path or URL: {str(re)}")
    return data

#https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False
