from _pytest.mark import param
from pytest import mark
from pytest_lazyfixture import lazy_fixture

from kgforge.core.mapping import Mapper


class TestResources:

    @mark.parametrize("data", [
        param(lazy_fixture("record_path"), id="file"),
        param(lazy_fixture("records_path"), id="directory"),
        param(lazy_fixture("record"), id="record"),
        param(lazy_fixture("records"), id="records"),
    ])
    def test_map_from(self, mocker, forge, mapper, data):
        mocker.patch("kgforge.core.mapping.Mapper.apply")
        forge.resources.map_from(data, mapper)
        Mapper.apply.assert_called_once()
