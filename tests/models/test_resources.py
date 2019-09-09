from pytest import raises

from kgforge.core.models.resources import Resource, Resources


class TestResource:

    def test_init(self, make_resource, resource_properties):
        r = make_resource(resource_properties)
        for k, v in resource_properties.items():
            assert getattr(r, k) == v

    def test_init_reserved(self, make_resource, resource_reserved_attributes):
        for x in resource_reserved_attributes:
            with raises(NotImplementedError):
                make_resource({x: 3})

    def test_path(self, make_resource, resource_properties_nested):
        r = make_resource(resource_properties_nested)
        id_ = resource_properties_nested["agent"].id
        assert r.agent.id == id_

    def test_repr(self, resource):
        type_ = getattr(resource, "type", None)
        assert repr(resource) == f"Resource(type={type_}, id={resource.id})"

    def test_print(self, resource):
        assert str(resource)

    def test_to_dict(self, resource, resource_reserved_attributes):
        dict_ = resource._to_dict()
        assert set(resource_reserved_attributes).isdisjoint(set(dict_.keys()))
        for k, v in dict_.items():
            assert not isinstance(v, Resource)

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
