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

import pytest
from pytest_bdd import given, scenario, scenarios, then

from kgforge.core.resources import Resource, Resources


def _resources():
    r1 = Resource(index=0)
    r2 = Resource(index=1)
    return [r1, r2]


@pytest.mark.parametrize("collection", [
    pytest.param(_resources(), id="list"),
    pytest.param(iter(_resources()), id="iterator"),
])
@scenario(
    "resources.feature",
    "Create a Resources object from a collection of resources."
)
def test_creation(collection):
    pass


scenarios("resources.feature")


@given("I create a Resources object from a collection of resources.")
def resources(collection):
    return Resources(collection)


@given("I create a Resources object from existing resources.", target_fixture="resources")
def resources_():
    return Resources(_resources())


@then("I should be able to count the number of resources with len().")
def check_count(resources):
    assert len(resources) == 2


@then("The Resource objects should be in the same order as inserted.")
def check_order(resources):
    assert resources[0].index == 0
    assert resources[1].index == 1
