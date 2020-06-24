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

# Placeholder for the test suite for reshaping.
import pytest
from kgforge.core import Resource
from kgforge.core.reshaping import collect_values


def test_collect_values():
    simple = Resource(type="Experiment", url="file.gz")
    r = collect_values(simple, "url")
    assert simple.url in r, "url should be in the list"
    deep = Resource(type="Experiment", level1=Resource(level2=Resource(url="file.gz")))
    r = collect_values(deep, "level1.level2.url")
    assert deep.level1.level2.url in r, "url should be in the list"
    files = [Resource(type="Experiment", url=f"file{i}") for i in range(3)]
    r = collect_values(files, "url")
    assert ["file0", "file1", "file2"] == r, "three elements should be in the list"
    data_set = Resource(type="Dataset", hasPart=files)
    r = collect_values(data_set, "hasPart.url")
    assert ["file0", "file1", "file2"] == r, "three elements should be in the list"
    with pytest.raises(ValueError):
        collect_values(data_set, "fake.path", ValueError)
