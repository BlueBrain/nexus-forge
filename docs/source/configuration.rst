Configuration
=============

YAML
----

The full `KnowledgeGraphForge` YAML configuration has the following structure:

.. code-block:: yaml

   Model:
     name: <a class name of a Model>
     origin: <'directory', 'url', or 'store'>
     source: <a directory path, an URL, or the class name of a Store>
     bucket: <when 'origin' is 'store', a Store bucket, a section or segment in the Store>
     endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
     token: <when 'origin' is 'store', a Store token, default to Store:token>
     context: <when a 'origin' is 'store', a Store token, default to Model:token>
       iri: <an IRI>
       bucket: <when 'origin' is 'store', a Store bucket, default to Model:bucket>
       endpoint: <when 'origin' is 'store', a Store endpoint, default to Model:endpoint>
       token: <when 'origin' is 'store', a Store token, default to Model:token>
   Store:
     name: <a class name of a Store>
     endpoint: <an URL>
     bucket: <a bucket as a string>
     token: <a token as a string>
     searchendpoints:
        <querytype>: <a query paradigm supported by configured store (e.g. sparql)>
          endpoint: <an IRI of a query endpoint>
     versioned_id_template: <a string template using 'x' to access resource fields>
     file_resource_mapping: <an Hjson string, a file path, or an URL>
   Resolvers:
     <scope>:
       - resolver: <a class name of a Resolver>
         origin: <'directory', 'web_service', or 'store'>
         source: <a directory path, a web service endpoint, or the class name of a Store>
         targets:
           - identifier: <a name, or an IRI>
             bucket: <a file name, an URL path, or a Store bucket>
         resolve_with_properties: <a list of str currently only supported by DemoResolver>
         result_resource_mapping: <an Hjson string, a file path, or an URL>
         endpoint: <when 'origin' is 'store', a Store endpoint, default to Store:endpoint>
         token: <when 'origin' is 'store', a Store token, default to Store:token>
   Formatters:
     <identifier>: <a string template with replacement fields delimited by braces, i.e. '{}'>

JSON
----
The corresponding python configuration file would be like:

.. code-block:: python

   {
       "Model": {
           "name": <str>,
           "origin": <str>,
           "source": <str>,
           "bucket": <str>,
           "endpoint": <str>,
           "token": <str>,
           "context": {
                 "iri": <str>,
                 "bucket": <str>,
                 "endpoint": <str>,
                 "token": <str>,
           }
       },
       "Store": {
           "name": <str>,
           "endpoint": <str>,
           "bucket": <str>,
           "token": <str>,
           "searchendpoints": {
                "<querytype>": {
                "endpoint": <str>
            }
           },
           "versioned_id_template": <str>,
           "file_resource_mapping": <str>,
       },
       "Resolvers": {
           "<scope>": [
               {
                   "resolver": <str>,
                   "origin": <str>,
                   "source": <str>,
                   "targets": [
                       {
                           "identifier": <str>,
                           "bucket": <str>,
                       },
                       ...,
                   ],
                   "resolve_with_properties":[str],
                   "result_resource_mapping": <str>,
                   "endpoint": <str>,
                   "token": <str>,
               },
               ...,
           ],
       },
       "Formatters": {
           "<name>": <str>,
           ...,
       },
   }
