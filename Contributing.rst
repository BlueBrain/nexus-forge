Contributing
============

Please add `@MFSY` or `@crisely09` as a reviewer if your Pull Request modifies `core`.

Setup

.. code-block:: shell

   git clone https://github.com/BlueBrain/nexus-forge
   pip install --editable kgforge[dev]

Checks before committing

.. code-block:: shell

   tox

Styling
-------

`PEP 8 <https://www.python.org/dev/peps/pep-0008/>`__,
`PEP 257 <https://www.python.org/dev/peps/pep-0257/>`__, and
`PEP 20 <https://www.python.org/dev/peps/pep-0020/>`__ must be followed.

Releasing
---------

.. code-block:: shell

   # Setup
   pip install --upgrade pip setuptools wheel twine

   # Checkout
   git checkout master
   git pull upstream master

   # Check
   tox

   # Tag
   git tag -a v<x>.<y>.<z> HEAD
   git push upstream v<x>.<y>.<z>

   # Build
   python setup.py sdist bdist_wheel

   # Upload
   twine upload dist/*

   # Clean
   rm -R build dist *.egg-info

Generating locally the documentation
------------------------------------


.. code-block:: shell

   # Install sphinx-build and related packages
   pip install .[docs]

   # cd to the docs directory
   cd docs

   # Generate the docs
   sphinx-build -T -W --keep-going -b html -d _build/doctrees -c ./source -D language=en ./source _build/html

Signing the CLA
---------------

If you are not part of the Blue Brain project, a Contributor License Agreement (CLA) must be signed for any code changes
to be accepted. Please contact the `Forge Nexus team <mailto:bbp-ou-dke@groupes.epfl.ch>`__ to get the latest CLA version and
instructions.
