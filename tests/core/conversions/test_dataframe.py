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

import numpy as np
import pytest
from pandas import DataFrame


# Test suite for conversion of resource to / from Pandas DataFrame.

from kgforge.core import Resource


@pytest.fixture
def df_from_one_resource():
    return DataFrame({
        "id": {0: "123"},
        "type": {0: "Type"},
        "p1": {0: "v1a"},
        "p2": {0: "v2a"}
    })


@pytest.fixture
def df_expanded_from_one_resource():
    return DataFrame({
        "@type": {0: "schema:Person"},
        "schema:name": {0: "John Doe"}
    })


@pytest.fixture
def df():
    return DataFrame({
        "id": {0: "123", 1: "345"},
        "type": {0: "Type", 1: "Type"},
        "p1": {0: "v1a", 1: "v1b"},
        "p2": {0: "v2a", 1: "v2b"}
    })


@pytest.fixture
def ndf():
    return DataFrame({
        "id": {0: "678", 1: "912"},
        "type": {0: "Other", 1: "Other"},
        "p3": {0: "v3c", 1: "v3d"},
        "p4.id": {0: "123", 1: "345"},
        "p4.type": {0: "Type", 1: "Type"},
        "p4.p1": {0: "v1a", 1: "v1b"},
        "p4.p2": {0: "v2a", 1: "v2b"}
    })


class TestConversionToDataFrame:

    def test_as_dataframe_basic(self, forge, df, df_from_one_resource, r1, r2):
        assert(isinstance(r1, Resource))
        x = forge.as_dataframe(r1)
        assert x.equals(df_from_one_resource)

        rcs = [r1, r2]
        x = forge.as_dataframe(rcs)
        assert x.equals(df)

    def test_as_dataframe_expanded(self, forge, df_expanded_from_one_resource):
        r = Resource(type="Person", name="John Doe")
        x = forge.as_dataframe(r, expanded=True)
        assert x.equals(df_expanded_from_one_resource)

    def test_as_dataframe_metadata(self, forge, df, r1, r2):
        rcs = [r1, r2]
        forge.register(rcs)
        x = forge.as_dataframe(rcs, store_metadata=True)
        df["deprecated"] = [False, False]
        df["version"] = [1, 1]
        assert x.equals(df)

    def test_as_dataframe_missing(self, forge, df, r1, r2):
        # A Resource is missing a property.
        del r2.p1
        rcs = [r1, r2]
        x = forge.as_dataframe(rcs)
        df["p1"][1] = np.nan
        assert x.equals(df)

    def test_as_dataframe_na_none(self, forge, df, r1, r2):
        # A Resource has one property with a value which represents a missing value.
        r2.p1 = None
        rcs = [r1, r2]
        x = forge.as_dataframe(rcs)
        df["p1"][1] = np.nan
        assert x.equals(df)

    def test_as_dataframe_na_string(self, forge, df, r1, r2):
        # A Resource has one property with a value which represents a missing value.
        r2.p1 = "(missing)"
        rcs = [r1, r2]
        x = forge.as_dataframe(rcs, na="(missing)")
        df["p1"][1] = np.nan
        assert x.equals(df)

    def test_as_dataframe_na_strings(self, forge, df, r1, r2):
        # A Resource has two properties with two different values which represent a missing value.
        r1.p2 = "NA"
        r2.p1 = "(missing)"
        rcs = [r1, r2]
        x = forge.as_dataframe(rcs, na=["NA", "(missing)"])
        df["p2"][0] = np.nan
        df["p1"][1] = np.nan
        assert x.equals(df)

    def test_as_dataframe_nesting_default_depth_1(self, ndf, forge, r3, r4):
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs)
        assert x.equals(ndf)

    def test_as_dataframe_nesting_default_depth_2(self, forge, ndf, r1, r2, r3, r4, r5):
        r1.p2 = r5
        del r2.p2
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs)
        ndf.drop("p4.p2", axis=1, inplace=True)
        ndf["p4.p2.p5"] = ["v5e", np.nan]
        ndf["p4.p2.p6"] = ["v6e", np.nan]
        assert x.equals(ndf)

    def test_as_dataframe_nesting_specific(self, forge, ndf, r3, r4):
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs, nesting="__")
        ndf.rename(columns={
            "p4.id": "p4__id",
            "p4.type": "p4__type",
            "p4.p1": "p4__p1",
            "p4.p2": "p4__p2",
        }, inplace=True)
        assert x.equals(ndf)

    def test_as_dataframe_nested_missing(self, forge, ndf, r2, r3, r4):
        del r2.p1
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs)
        ndf["p4.p1"][1] = np.nan
        assert x.equals(ndf)

    def test_as_dataframe_nested_na_none(self, forge, ndf, r2, r3, r4):
        r2.p1 = None
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs)
        ndf["p4.p1"][1] = np.nan
        assert x.equals(ndf)

    def test_as_dataframe_nested_na_string(self, forge, ndf, r2, r3, r4):
        r2.p1 = "(missing)"
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs, na="(missing)")
        ndf["p4.p1"][1] = np.nan
        assert x.equals(ndf)

    def test_as_dataframe_nested_na_strings(self, forge, ndf, r1, r2, r3, r4):
        r1.p2 = "NA"
        r2.p1 = "(missing)"
        rcs = [r3, r4]
        x = forge.as_dataframe(rcs, na=["NA", "(missing)"])
        ndf["p4.p2"][0] = np.nan
        ndf["p4.p1"][1] = np.nan
        assert x.equals(ndf)


class TestConversionFromDataFrame:

    def test_from_dataframe_basic_row(self, forge, df, r1):
        df.drop(1, inplace=True)
        x = forge.from_dataframe(df)
        assert x == r1

    def test_from_dataframe_basic_rows(self, forge, df, r1, r2):
        x = forge.from_dataframe(df)
        rcs = [r1, r2]
        assert x == rcs

    def test_from_dataframe_na_none(self, forge, df, r1, r2):
        # A cell has a value which represents a missing value.
        df["p1"][1] = None
        x = forge.from_dataframe(df)
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_dataframe_na_string(self, forge, df, r1, r2):
        # A cell has a value which represents a missing value.
        df["p1"][1] = "(missing)"
        x = forge.from_dataframe(df, na="(missing)")
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_dataframe_na_strings(self, forge, df, r1, r2):
        # Two cells have two different values which represent a missing value.
        df["p2"][0] = "NA"
        df["p1"][1] = "(missing)"
        x = forge.from_dataframe(df, na=["NA", "(missing)"])
        del r1.p2
        del r2.p1
        rcs = [r1, r2]
        assert x == rcs

    def test_from_dataframe_nesting_default_depth_1(self, ndf, forge, r3, r4):
        x = forge.from_dataframe(ndf)
        rcs = [r3, r4]
        assert x == rcs

    def test_from_dataframe_nesting_default_depth_2(self, forge, ndf, r1, r2, r3, r4, r5):
        ndf.drop("p4.p2", axis=1, inplace=True)
        ndf["p4.p2.p5"] = ["v5e", np.nan]
        ndf["p4.p2.p6"] = ["v6e", np.nan]
        x = forge.from_dataframe(ndf)
        r1.p2 = r5
        del r2.p2
        rcs = [r3, r4]
        assert x == rcs

    def test_from_dataframe_nesting_specific(self, forge, ndf, r3, r4):
        ndf.rename(columns={
            "p4.id": "p4__id",
            "p4.type": "p4__type",
            "p4.p1": "p4__p1",
            "p4.p2": "p4__p2",
        }, inplace=True)
        x = forge.from_dataframe(ndf, nesting="__")
        rcs = [r3, r4]
        assert x == rcs

    def test_from_dataframe_nesting_na_none(self, forge, ndf, r2, r3, r4):
        ndf["p4.p1"][1] = None
        x = forge.from_dataframe(ndf)
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs

    def test_from_dataframe_nesting_na_string(self, forge, ndf, r2, r3, r4):
        ndf["p4.p1"][1] = "(missing)"
        x = forge.from_dataframe(ndf, na="(missing)")
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs

    def test_from_dataframe_nesting_na_strings(self, forge, ndf, r1, r2, r3, r4):
        ndf["p4.p2"][0] = "NA"
        ndf["p4.p1"][1] = "(missing)"
        x = forge.from_dataframe(ndf, na=["NA", "(missing)"])
        del r1.p2
        del r2.p1
        rcs = [r3, r4]
        assert x == rcs
