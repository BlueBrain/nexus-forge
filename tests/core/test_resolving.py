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

from kgforge.core.archetypes.resolver import escape_punctuation, write_sparql_filters


@pytest.mark.parametrize(
    "text,expected",
    [
    pytest.param(("My label"), ("My label"),
        id="nothing"),
    pytest.param(("My label-"), ("My label\\\\-"),
        id="dash"),
    pytest.param(("My/label"), ("My\\\\/label"),
        id="slash"),
    pytest.param(("My +label"), ("My \\\\+label"),
        id="plus"),
    pytest.param(("My {}label"), ("My \\\\{\\\\}label"),
        id="curly_brackets"),
    pytest.param(("My <label>"), ("My \\\\<label\\\>"),
        id="brackets"),
    pytest.param(("My@label yay"), ("My\\\\@label yay"),
        id="atsymbol"),
    pytest.param(("My label: something."), ("My label\\\\: something\\\\."),
        id="dots"),
    pytest.param(("My label?!"), ("My label\\\\?\\\\!"),
        id="marks"),
    pytest.param(("The rest, ~ | are here # ;"),
        ("The rest\\\\, \\\\~ \\\\| are here \\\\# \\\\;"),
        id="rest")
    ]
)
def test_escape_punctuation(text, expected):
    new_text = escape_punctuation(text)
    assert new_text == expected

@pytest.fixture
def text():
    return "My nice text"

@pytest.fixture
def check_text():
    return "Label/with_Different+ Symbols."

agent_properties = ["name", "givenName", "familyName"]
ontology_properties = ['label', 'notation', 'prefLabel', 'altLabel']

def test_write_filters_params(text):
    with pytest.raises(ValueError):
        write_sparql_filters(text, ['name'], case_insensitive=True)

@pytest.mark.parametrize(
    "properties,params,expected",
    [
    pytest.param((agent_properties), ({}),
        ([' FILTER (?name = "My nice text")',
          ' FILTER (?givenName = "My nice text")',
          ' FILTER (?familyName = "My nice text")'],
         ),
        id="agent filters",
        ),
    pytest.param((agent_properties), ({'regex': True}),
        ([' FILTER regex(?name, "My nice text")',
          ' FILTER regex(?givenName, "My nice text")',
          ' FILTER regex(?familyName, "My nice text")'],
         ),
        id="agent filters regex",
        ),
    pytest.param((agent_properties), ({'regex': True, 'case_insensitive': True}),
        ([' FILTER regex(?name, "My nice text", \"i\")',
          ' FILTER regex(?givenName, "My nice text", \"i\")',
          ' FILTER regex(?familyName, "My nice text", \"i\")'],
         ),
        id="agent filters all",
        ),
    pytest.param((ontology_properties), ({}),
        ([' FILTER (?label = "My nice text")',
          ' FILTER (?notation = "My nice text")',
          ' FILTER (?prefLabel = "My nice text")',
          ' FILTER (?altLabel = "My nice text")'],
         ),
        id="ontology filters",
        ),
    pytest.param((ontology_properties), ({'regex': True, 'case_insensitive': True}),
        ([' FILTER regex(?label, "My nice text", \"i\")',
          ' FILTER regex(?notation, "My nice text", \"i\")',
          ' FILTER regex(?prefLabel, "My nice text", \"i\")',
          ' FILTER regex(?altLabel, "My nice text", \"i\")'],
         ),
        id="ontology filters",
        ),
    ]
)
def test_write_sparql_filters(text, properties, params, expected):
    filters = write_sparql_filters(text, properties, **params)
    assert filters == expected[0]