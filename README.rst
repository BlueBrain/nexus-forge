Blue Brain Nexus Forge
======================

|Travis_badge| |Version Status| |Binder|

.. image:: https://raw.githubusercontent.com/BlueBrain/nexus-forge/master/docs/source/assets/bbnforge

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

The `examples <https://github.com/BlueBrain/nexus-forge/tree/master/examples/notebooks>`__
directory contains many Jupyter Notebooks to get started with
Blue Nexus Forge user features and usage scenarios.

You can run the Getting Started notebooks on Binder by clicking on |Binder|.

For local execution, make sure that the ``jupyter notebook|lab`` is launched
in the same virtual environment where Blue Brain Nexus Forge is installed.
Alternatively, set up a specialized
`kernel <https://ipython.readthedocs.io/en/stable/install/kernel_install.html>`__.

In both cases, please start with the notebook named *00 - Initialization*.
It contains instructions for configuring the Forge with:

- an example in-memory store and an example schema language,
- Blue Brain Nexus as store and W3C SHACL as schema language.

After, it is recommended to run the notebooks following their number (01, 02, ...).

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



Funding and Acknowledgements
----------------------------

This project has received funding from the EPFL Blue Brain Project (funded by
the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology)
and from the European Union’s Horizon 2020 Framework Programme for Research and
Innovation under the Specific Grant Agreement No. 785907 (Human Brain Project SGA2).


COPYRIGHT © 2019–2021 Blue Brain Project/EPFL

.. |Binder| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/master?filepath=examples%2Fnotebooks%2Fgetting-started
    
.. |Travis_badge| image:: https://travis-ci.com/BlueBrain/nexus-forge.svg?branch=master
    :target: https://travis-ci.com/BlueBrain/nexus-forge 

.. |Version Status| image:: https://img.shields.io/pypi/v/nexusforge.svg
   :target: https://pypi.python.org/pypi/nexusforge

