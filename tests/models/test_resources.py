from pytest import raises

from kgforge.core.models.resources import Resource, Resources


class TestResource:

    def test_init(self, make_resource, properties):
        r = make_resource(properties)
        for k, v in properties.items():
            assert getattr(r, k) == v

    def test_init_reserved(self, forge, make_resource):
        r = Resource(forge)
        for x in r.__dict__.keys():
            with raises(NotImplementedError):
                make_resource({x: 3})

    def test_path(self, make_resource, properties_with_resource):
        r = make_resource(properties_with_resource)
        id_ = properties_with_resource["agent"].id
        assert r.agent.id == id_

    def test_repr(self, resource):
        type_ = getattr(resource, "type", None)
        assert repr(resource) == f"Resource(type={type_}, id={resource.id})"

    def test_print(self, resource):
        assert str(resource)

    def test_to_dict(self, resource):
        assert resource._to_dict()

    def test_to_dict_added(self, make_resource):
        name_ = "Jane Doe"
        r = make_resource()
        r.name = name_
        converted = r._to_dict()
        assert converted["name"] == name_


class TestResources:

    def test_init(self, resources):
        rs = Resources(resources)
        for x, y in zip(resources, rs):
            assert x == y

    def test_list(self, resources):
        rs = Resources(resources)
        assert isinstance(rs, list)
