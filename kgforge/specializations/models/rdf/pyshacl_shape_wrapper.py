from pyshacl import Shape, ShapesGraph
from rdflib import Graph, URIRef
from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS

from typing import List, Optional, Set, Tuple, Dict

from kgforge.specializations.models.rdf.collectors import ALL_COLLECTORS


ALL_COLLECTORS_MAP = {c.constraint(): c for c in ALL_COLLECTORS}


class ShapeWrapper(Shape):
    __slots__ = ('__dict__',)

    def __init__(self, shape: Shape) -> None:
        super().__init__(shape.sg, shape.node, shape._p, shape._path, shape.logger)

    def parameters(self):
        return (
            p for p, v in self.sg.predicate_objects(self.node)
            if p in ALL_CONSTRAINT_PARAMETERS
        )

    def traverse(self, predecessors: Set[URIRef]) -> Tuple[List, Dict]:
        """ traverses the Shape SHACL properties to collect constrained properties

        This function is injected to pyshacl Shape object in order to traverse the Shacl graph.
        It will call a specific collector depending on the SHACL property present in the NodeShape

        Args:
            predecessors: list of nodes that have being traversed, used to break circular
                recursion

        Returns:
            properties, attributes: Tuple(list,dict), the collected properties and attributes
                respectively gathered from the collectors
        """

        parameters = self.parameters()
        properties = list()
        attributes = dict()
        done_collectors = set()
        for param in iter(parameters):
            if param in ALL_COLLECTORS_MAP:
                constraint_collector = ALL_COLLECTORS_MAP[param]
                if constraint_collector not in done_collectors:
                    c = constraint_collector(self)
                    predecessors.add(self.node)
                    props, attrs = c.collect(predecessors)
                    if attrs:
                        attributes.update(attrs)
                    if props:
                        properties.extend(props)
                    done_collectors.add(constraint_collector)
                    if predecessors:
                        predecessors.remove(self.node)
            else:
                # FIXME: there are some SHACL constrains that are not implemented
                # raise IndexError(f"{param} not implemented!")
                pass

        return properties, attributes


class ShapesGraphWrapper(ShapesGraph):

    def __init__(self, graph: Graph) -> None:
        super().__init__(graph)
        # the following line triggers the shape loading -> see pyshacl.ShapesGraph
        self._shapes = self.shapes

    def lookup_shape_from_node(self, node: URIRef) -> Optional[ShapeWrapper]:
        """ Overwrite function to inject the transverse function for only to requested nodes.

        Args:
            node (URIRef): The node to look up.

        Returns:
            Shape: The Shacl shape of the requested node.
        """
        shape: Shape = self._node_shape_cache.get(node, None)
        if shape:
            return ShapeWrapper(shape)
            # if not hasattr(shape_wrapper, "traverse"):
            #     shape_wrapper.traverse = types.MethodType(traverse, shape_wrapper)
            # return shape_wrapper
        return None
