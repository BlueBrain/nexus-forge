Tutorials
=========

Getting Started
---------------

Nexus Forge includes detailed notebooks which demonstrate its capabilities and
and can be used as tutorials for each piece of its functionality.

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

.. |Binder| image:: https://mybinder.org/badge_logo.svg
    :alt: Binder
    :target: https://mybinder.org/v2/gh/BlueBrain/nexus-forge/master?filepath=examples%2Fnotebooks%2Fgetting-started
