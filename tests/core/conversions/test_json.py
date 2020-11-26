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

import pytest


# Test suite for conversion of a resource to / from JSON.

@pytest.fixture
def json_many():
    return [
        {
            "id": "123",
            "type": "Type",
            "p1": "v1a",
            "p2": "v2a"
        },
        {
            "id": "345",
            "type": "Type",
            "p1": "v1b",
            "p2": "v2b"
        }
    ]


@pytest.fixture
def json_nested_many():
    return [
        {
            "id": "678",
            "type": "Other",
            "p3": "v3c",
            "p4": {
                "id": "123",
                "type": "Type",
                "p1": "v1a",
                "p2": "v2a"
            }
        },
        {
            "id": "912",
            "type": "Other",
            "p3": "v3d",
            "p4": {
                "id": "345",
                "type": "Type",
                "p1": "v1b",
                "p2": "v2b"
            }
        }
    ]


class TestConversionFromJson:

    def test_from_json_basic_one(self, forge, json_one, r1):
        x = forge.from_json(json_one)
        assert x == r1

    def test_from_json_list_resources_one(self, forge, json_list_one, r1, r2, r3):
        x = forge.from_json(json_list_one)
        r3.p4 = [r1, r2]
        assert x == r3

    def test_from_json_list_mixed_one(self, forge, json_list_one, r1, r2, r3):
        json_list_one["p4"].insert(1, "543")
        x = forge.from_json(json_list_one)
        r3.p4 = [r1, "543", r2]
        assert x == r3

    def test_from_json_basic_many(self, forge, json_many, r1, r2):
        x = forge.from_json(json_many)
        rcs = [r1, r2]
        assert x == rcs

    def test_from_json_na_none(self, forge, json_many, r1, r2):
        json_many[1]["p1"] = None
        x = forge.from_json(json_many)
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_json_na_string(self, forge, json_many, r1, r2):
        json_many[1]["p1"] = "(missing)"
        x = forge.from_json(json_many, na="(missing)")
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_json_na_strings(self, forge, json_many, r1, r2):
        json_many[0]["p2"] = "NA"
        json_many[1]["p1"] = "(missing)"
        x = forge.from_json(json_many, na=["NA", "(missing)"])
        del r1.p2
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_json_nested_default_depth_1(self, json_nested_many, forge, r3, r4):
        x = forge.from_json(json_nested_many)
        rcs = [r3, r4]
        assert x == rcs

    def test_from_json_nested_default_depth_2(self, forge, json_nested_many, r1, r3, r4, r5):
        json_nested_many[0]["p4"]["p2"] = {"p5": "v5e", "p6": "v6e"}
        x = forge.from_json(json_nested_many)
        r1.p2 = r5
        rcs = [r3, r4]
        assert x == rcs

    def test_from_json_nested_na_none(self, forge, json_nested_many, r2, r3, r4):
        json_nested_many[1]["p4"]["p1"] = None
        x = forge.from_json(json_nested_many)
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs

    def test_from_json_nested_na_string(self, forge, json_nested_many, r2, r3, r4):
        json_nested_many[1]["p4"]["p1"] = "(missing)"
        x = forge.from_json(json_nested_many, na="(missing)")
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs

    def test_from_json_nested_na_strings(self, forge, json_nested_many, r1, r2, r3, r4):
        json_nested_many[0]["p4"]["p2"] = "NA"
        json_nested_many[1]["p4"]["p1"] = "(missing)"
        x = forge.from_json(json_nested_many, na=["NA", "(missing)"])
        del r1.p2
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs
