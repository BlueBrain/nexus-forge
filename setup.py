import os

from setuptools import setup

VERSION = "0.1.0.dev3"

HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="kgforge",
    author="BlueBrain DKE",
    author_email="bbp-ou-dke@groupes.epfl.ch",
    version=VERSION,
    description="Framework building a bridge between data engineers,"
                "knowledge engineers, and (data) scientists in the context of"
                "knowledge graphs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="data knowledge scientists graph",
    url="https://github.com/BlueBrain/kgforge",
    packages=["kgforge"],
    python_requires=">=3.6",
    install_requires=[
        "hjson",
        "pandas",
    ],
    extras_require={
        "dev": ["pytest", "pytest-cov", "pytest-mock", "pytest-lazy-fixture"],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3 :: Only",
        "Natural Language :: English",
    ]
)
