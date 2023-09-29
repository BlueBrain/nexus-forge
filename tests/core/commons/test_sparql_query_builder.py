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

from kgforge.core.commons.context import Context
from kgforge.core.commons.sparql_query_builder import SPARQLQueryBuilder
from kgforge.core.resource import Resource
import pytest


class TestSPARQLQueryBuilder:
    @pytest.mark.parametrize(
        "query, response, resource_json",
        [
            pytest.param(
                ("""
                    PREFIX bmc: <https://bbp.epfl.ch/ontologies/core/bmc/>
                    PREFIX bmo: <https://bbp.epfl.ch/ontologies/core/bmo/>
                    PREFIX commonshapes: <https://neuroshapes.org/commons/>
                    PREFIX datashapes: <https://neuroshapes.org/dash/>
                    PREFIX dc: <http://purl.org/dc/elements/1.1/>
                    PREFIX dcat: <http://www.w3.org/ns/dcat#>
                    PREFIX dcterms: <http://purl.org/dc/terms/>
                    PREFIX mba: <http://api.brain-map.org/api/v2/data/Structure/>
                    PREFIX nsg: <https://neuroshapes.org/>
                    PREFIX nxv: <https://bluebrain.github.io/nexus/vocabulary/>
                    PREFIX oa: <http://www.w3.org/ns/oa#>
                    PREFIX obo: <http://purl.obolibrary.org/obo/>
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX prov: <http://www.w3.org/ns/prov#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX schema: <http://schema.org/>
                    PREFIX sh: <http://www.w3.org/ns/shacl#>
                    PREFIX shsh: <http://www.w3.org/ns/shacl-shacl#>
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX vann: <http://purl.org/vocab/vann/>
                    PREFIX void: <http://rdfs.org/ns/void#>
                    PREFIX xml: <http://www.w3.org/XML/1998/namespace/>
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

                            CONSTRUCT {
                                ?id a ?type ;
                                rdfs:label ?label ;
                                skos:prefLabel ?prefLabel ;
                                skos:altLabel ?altLabel ;
                                skos:definition ?definition;
                                rdfs:subClassOf ?subClassOf ;
                                rdfs:isDefinedBy ?isDefinedBy ;
                                skos:notation ?notation ;
                                skos:definition ?definition ;
                                nsg:atlasRelease ?atlasRelease ;
                                schema:identifier ?identifier ;
                                <https://bbp.epfl.ch/ontologies/core/bmo/delineatedBy> ?delineatedBy ;
                                <https://neuroshapes.org/hasLayerLocationPhenotype> ?hasLayerLocationPhenotype ;
                                <https://bbp.epfl.ch/ontologies/core/bmo/representedInAnnotation> ?representedInAnnotation ;
                                schema:isPartOf ?isPartOf ;
                                <https://bbp.epfl.ch/ontologies/core/bmo/isLayerPartOf> ?isLayerPartOf .
                            } WHERE {
                                GRAPH ?g {
                                    ?id a ?type ;
                                        rdfs:label ?label ; 
                                    OPTIONAL {
                                    ?id rdfs:subClassOf ?subClassOf ;
                                    }
                                    OPTIONAL {
                                    ?id skos:definition ?definition ;
                                    }
                                    OPTIONAL {
                                    ?id skos:prefLabel ?prefLabel .
                                    }
                                    OPTIONAL {
                                    ?id skos:altLabel ?altLabel .
                                    }
                                    OPTIONAL {
                                    ?id rdfs:isDefinedBy ?isDefinedBy .
                                    }     
                                    OPTIONAL {
                                    ?id skos:notation ?notation .
                                    }    
                                    OPTIONAL {
                                    ?id skos:definition ?definition .
                                    }    
                                    OPTIONAL {
                                    ?id nsg:atlasRelease ?atlasRelease .
                                    }    
                                    OPTIONAL {
                                    ?id <https://neuroshapes.org/hasLayerLocationPhenotype> ?hasLayerLocationPhenotype .
                                    }    
                                    OPTIONAL {
                                    ?id schema:identifier ?identifier .
                                    }    
                                    OPTIONAL {
                                    ?id <https://bbp.epfl.ch/ontologies/core/bmo/delineatedBy> ?delineatedBy .
                                    }    
                                    OPTIONAL {
                                    ?id <https://bbp.epfl.ch/ontologies/core/bmo/representedInAnnotation> ?representedInAnnotation .
                                    }    
                                    OPTIONAL {
                                    ?id schema:isPartOf ?isPartOf .
                                    }    
                                    OPTIONAL {
                                    ?id <https://bbp.epfl.ch/ontologies/core/bmo/isLayerPartOf> ?isLayerPartOf .
                                    }    
                                    OPTIONAL {
                                    ?id <https://neuroshapes.org/units> ?units .
                                    }    
                                    {
                                    SELECT * WHERE {
                                        { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a owl:Class ; 
                    rdfs:subClassOf* nsg:BrainRegion ; rdfs:label ?label  FILTER (?label = "Isocortex") } UNION
                                        { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a owl:Class ; 
                    rdfs:subClassOf* nsg:BrainRegion ; skos:notation ?notation  FILTER (?notation = "Isocortex") } UNION
                                        { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a owl:Class ; 
                    rdfs:subClassOf* nsg:BrainRegion ; skos:prefLabel ?prefLabel  FILTER (?prefLabel = "Isocortex") } UNION
                                        { ?id <https://bluebrain.github.io/nexus/vocabulary/deprecated> "false"^^xsd:boolean ; a owl:Class ; 
                    rdfs:subClassOf* nsg:BrainRegion ; skos:altLabel ?altLabel  FILTER (?altLabel = "Isocortex") }
                                    } LIMIT 1
                                    }
                                }
                            }
                """),
                ({
    "head": {
        "vars": [
            "subject",
            "predicate",
            "object",
            "context"
        ]
    },
    "results": {
        "bindings": [
            {
                "object": {
                    "type": "uri",
                    "value": "http://www.w3.org/2002/07/owl#Class"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "literal",
                    "value": "Isocortex"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/2000/01/rdf-schema#label"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "literal",
                    "value": "Isocortex"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/2004/02/skos/core#prefLabel"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "uri",
                    "value": "https://neuroshapes.org/BrainRegion"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/2000/01/rdf-schema#subClassOf"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "uri",
                    "value": "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/2000/01/rdf-schema#isDefinedBy"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "literal",
                    "value": "Isocortex"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://www.w3.org/2004/02/skos/core#notation"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "uri",
                    "value": "https://bbp.epfl.ch/neurosciencegraph/data/4906ab85-694f-469d-962f-c0174e901885"
                },
                "predicate": {
                    "type": "uri",
                    "value": "https://neuroshapes.org/atlasRelease"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                    "type": "literal",
                    "value": "315"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://schema.org/identifier"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "uri",
                    "value": "http://purl.obolibrary.org/obo/UBERON_0001950"
                },
                "predicate": {
                    "type": "uri",
                    "value": "https://bbp.epfl.ch/ontologies/core/bmo/delineatedBy"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "datatype": "http://www.w3.org/2001/XMLSchema#boolean",
                    "type": "literal",
                    "value": "true"
                },
                "predicate": {
                    "type": "uri",
                    "value": "https://bbp.epfl.ch/ontologies/core/bmo/representedInAnnotation"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            },
            {
                "object": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/695"
                },
                "predicate": {
                    "type": "uri",
                    "value": "http://schema.org/isPartOf"
                },
                "subject": {
                    "type": "uri",
                    "value": "http://api.brain-map.org/api/v2/data/Structure/315"
                }
            }
        ]
    }
}),
                ({
                    "id": "http://api.brain-map.org/api/v2/data/Structure/315",
                    "type": "Class",
                    "label": "Isocortex",
                    "atlasRelease":
                    {
                        "id": "https://bbp.epfl.ch/neurosciencegraph/data/4906ab85-694f-469d-962f-c0174e901885"
                    },
                    "delineatedBy": "obo:UBERON_0001950",
                    "identifier": 315,
                    "isDefinedBy": "http://bbp.epfl.ch/neurosciencegraph/ontologies/core/brainregion",
                    "isPartOf": "mba:695",
                    "notation": "Isocortex",
                    "prefLabel": "Isocortex",
                    "representedInAnnotation": True,
                    "subClassOf": "nsg:BrainRegion"
                }),
                id="from_construct_query",
            ),
            pytest.param(
                ("""
                    PREFIX bmc: <https://bbp.epfl.ch/ontologies/core/bmc/>
                    PREFIX bmo: <https://bbp.epfl.ch/ontologies/core/bmo/>
                    PREFIX commonshapes: <https://neuroshapes.org/commons/>
                    PREFIX datashapes: <https://neuroshapes.org/dash/>
                    PREFIX dc: <http://purl.org/dc/elements/1.1/>
                    PREFIX dcat: <http://www.w3.org/ns/dcat#>
                    PREFIX dcterms: <http://purl.org/dc/terms/>
                    PREFIX mba: <http://api.brain-map.org/api/v2/data/Structure/>
                    PREFIX nsg: <https://neuroshapes.org/>
                    PREFIX nxv: <https://bluebrain.github.io/nexus/vocabulary/>
                    PREFIX oa: <http://www.w3.org/ns/oa#>
                    PREFIX obo: <http://purl.obolibrary.org/obo/>
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX prov: <http://www.w3.org/ns/prov#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX schema: <http://schema.org/>
                    PREFIX sh: <http://www.w3.org/ns/shacl#>
                    PREFIX shsh: <http://www.w3.org/ns/shacl-shacl#>
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX vann: <http://purl.org/vocab/vann/>
                    PREFIX void: <http://rdfs.org/ns/void#>
                    PREFIX xml: <http://www.w3.org/XML/1998/namespace/>
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                    PREFIX : <https://bbp.epfl.ch/ontologies/core/bmo/>
                    SELECT ?id ?_constrainedBy ?_createdAt ?_createdBy ?_deprecated ?_incoming ?_outgoing ?_project ?_rev ?_schemaProject ?_self ?_updatedAt ?_updatedBy WHERE { Graph ?g {?id rdfs:label ?v0;
                    <https://bluebrain.github.io/nexus/vocabulary/constrainedBy> ?_constrainedBy;
                    <https://bluebrain.github.io/nexus/vocabulary/createdAt> ?_createdAt;
                    <https://bluebrain.github.io/nexus/vocabulary/createdBy> ?_createdBy;
                    <https://bluebrain.github.io/nexus/vocabulary/deprecated> ?_deprecated;
                    <https://bluebrain.github.io/nexus/vocabulary/incoming> ?_incoming;
                    <https://bluebrain.github.io/nexus/vocabulary/outgoing> ?_outgoing;
                    <https://bluebrain.github.io/nexus/vocabulary/project> ?_project;
                    <https://bluebrain.github.io/nexus/vocabulary/rev> ?_rev;
                    <https://bluebrain.github.io/nexus/vocabulary/schemaProject> ?_schemaProject;
                    <https://bluebrain.github.io/nexus/vocabulary/self> ?_self;
                    <https://bluebrain.github.io/nexus/vocabulary/updatedAt> ?_updatedAt;
                    <https://bluebrain.github.io/nexus/vocabulary/updatedBy> ?_updatedBy . 
                    FILTER(?v0 = "PV+").
                    Filter (?_deprecated = 'false'^^xsd:boolean)
                    }}  LIMIT 100
                """),
                ({
                    "head": {
                        "vars": [
                        "id",
                        "_constrainedBy",
                        "_createdAt",
                        "_createdBy",
                        "_deprecated",
                        "_incoming",
                        "_outgoing",
                        "_project",
                        "_rev",
                        "_schemaProject",
                        "_self",
                        "_updatedAt",
                        "_updatedBy"
                        ]
                    },
                    "results": {
                        "bindings": [
                        {
                            "id": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/ontologies/core/celltypes/PV_plus"
                            },
                            "_constrainedBy": {
                            "type": "uri",
                            "value": "https://neuroshapes.org/dash/ontologyentity"
                            },
                            "_createdAt": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#dateTime",
                            "type": "literal",
                            "value": "2022-08-29T12:54:15.376Z"
                            },
                            "_createdBy": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/sy"
                            },
                            "_deprecated": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#boolean",
                            "type": "literal",
                            "value": "false"
                            },
                            "_incoming": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus/incoming"
                            },
                            "_outgoing": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus/outgoing"
                            },
                            "_project": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/projects/neurosciencegraph/datamodels"
                            },
                            "_rev": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "36"
                            },
                            "_schemaProject": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/projects/neurosciencegraph/datamodels"
                            },
                            "_self": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus"
                            },
                            "_updatedAt": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#dateTime",
                            "type": "literal",
                            "value": "2023-09-28T10:52:04.387Z"
                            },
                            "_updatedBy": {
                            "type": "uri",
                            "value": "https://bbp.epfl.ch/nexus/v1/realms/serviceaccounts/users/service-account-brain-modeling-ontology-ci-cd"
                            }
                        }
                        ]
                    }
                    }),
                ({
                    "id": "https://bbp.epfl.ch/ontologies/core/celltypes/PV_plus",
                    "_constrainedBy": "https://neuroshapes.org/dash/ontologyentity",
                    "_createdAt": "2022-08-29T12:54:15.376Z",
                    "_createdBy": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/sy",
                    "_deprecated": False,
                    "_incoming": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus/incoming",
                    "_outgoing": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus/outgoing",
                    "_project": "https://bbp.epfl.ch/nexus/v1/projects/neurosciencegraph/datamodels",
                    "_rev": 36,
                    "_schemaProject": "https://bbp.epfl.ch/nexus/v1/projects/neurosciencegraph/datamodels",
                    "_self": "https://bbp.epfl.ch/nexus/v1/resources/neurosciencegraph/datamodels/_/https:%2F%2Fbbp.epfl.ch%2Fontologies%2Fcore%2Fcelltypes%2FPV_plus",
                    "_updatedAt": "2023-09-28T10:52:04.387Z",
                    "_updatedBy": "https://bbp.epfl.ch/nexus/v1/realms/serviceaccounts/users/service-account-brain-modeling-ontology-ci-cd"
                }),
                id="from_construct_query",
            )
        ]
    )
    def test_build_resource_from_response(
        self,
        query,
        response,
        resource_json,
        custom_context,
        forge
    ):
        custom_context_object = Context(custom_context, "http://store.org/metadata.json")
        results = SPARQLQueryBuilder.build_resource_from_response(query, response, custom_context_object)
        assert len(results) == 1
        assert isinstance(results[0], Resource)
        assert resource_json == forge.as_json(results[0])

  