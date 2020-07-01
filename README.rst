Blue Brain Nexus Forge
======================

Blue Brain Nexus Forge is a domain-agnostic, generic and extensible Python framework enabling
non-expert users to create and manage knowledge graphs by making it easy to:

- Discover and reuse available knowledge resources such as ontologies and
  schemas to shape, constraint, link and add semantics to datasets.
- Build knowledge graphs from datasets generated from heterogenous sources and formats.
  Defining, executing and sharing data mappers to transform data from a source format to a
  target one conformant to schemas and ontologies.
- Interface with various stores offering knowledge graph storage, management and
  scaling capabilities, for example Nexus Core store or in-memory store.
- Validate and register data and metadata.
- Search and download data and metadata from a knowledge graph.

Getting Started
---------------

The `examples <https://github.com/BlueBrain/nexus-forge/tree/master/examples/notebooks>`__ directory contains many jupyter notebooks to get started with Blue Nexus forge main features and usage scenarios.

Click on one of the following badges to launch the examples without download or install!. The notebook examples are numbered and it is recommended to run them in an ascending order.

* Demo examples using an in-memory store: |BinderDemo| |CollabDemo|
* Examples using Blue Brain Nexus as a store and W3C SHACL as schema language: |BinderNexus| |CollabNexus|

For local execution of the jupyter notebooks, make sure that the `jupyter notebook|lab` is launched in the same virtual environment where Blue Brain Nexus Forge is installed. Alternatively, set up a specialized `kernel <https://ipython.readthedocs.io/en/stable/install/kernel_install.html>`__.


Installation
------------

It is recommended to use a virtual environment such as `venv <https://docs.python.org/3.6/library/venv.html>`__ or
`conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`__.

Stable version

.. code-block:: shell

   pip install nexusforge

Upgrade to the latest version

.. code-block:: shell

   pip install --upgrade nexusforge

Development version

.. code-block:: shell

   pip install git+https://github.com/BlueBrain/nexus-forge



Acknowledgements
----------------

This project has received funding from the EPFL Blue Brain Project (funded by
the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology)
and from the European Union’s Horizon 2020 Framework Programme for Research and
Innovation under the Specific Grant Agreement No. 785907 (Human Brain Project SGA2).


.. |BinderNexus| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge.git/nexus-demo-notebooks?urlpath=tree%2Fexamples%2Fnotebooks%2Fnexus-demo

.. |CollabNexus| image:: https://colab.research.google.com/assets/colab-badge.svg
    :alt: Collab
    :target: https://colab.research.google.com/github/BlueBrain/nexus-forge/blob/nexus-demo-notebooks

.. |BinderDemo| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge.git/getting-started-notebooks?urlpath=tree%2Fexamples%2Fnotebooks%2Fgetting-started

.. |CollabDemo| image:: https://colab.research.google.com/assets/colab-badge.svg
    :alt: Collab
    :target: https://colab.research.google.com/github/BlueBrain/nexus-forge/blob/getting-started-notebooks
