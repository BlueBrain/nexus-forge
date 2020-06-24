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

# Placeholder for the test suite for actions.

from kgforge.core import Resource
from kgforge.core.commons.actions import LazyAction, collect_lazy_actions, execute_lazy_actions


def test_execute_lazy_actions():
    fun = lambda x: x
    ra = Resource(pa1="pa1",
                  pa2=Resource(pb1="pb1"),
                  pa3=LazyAction(fun, "pa3 executed"),
                  pa4=Resource(pc1=LazyAction(fun, "pc1 executed"), pc2="pc2"),
                  pa5=[LazyAction(fun, "pa5[0] executed"),
                       123,
                       Resource(pd1=LazyAction(fun, "pd1 executed")),
                       "string"])
    la = collect_lazy_actions(ra)
    execute_lazy_actions(ra, la)
    assert ra.pa1 == "pa1"
    assert ra.pa2.pb1 == "pb1"
    assert ra.pa3 == "pa3 executed"
    assert ra.pa4.pc1 == "pc1 executed"
    assert ra.pa4.pc2 == "pc2"
    assert ra.pa5[0] == "pa5[0] executed"
    assert ra.pa5[1] == 123
    assert ra.pa5[2].pd1 == "pd1 executed"
    assert ra.pa5[3] == "string"
