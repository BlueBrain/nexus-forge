# 
# Knowledge Graph Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Knowledge Graph Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Knowledge Graph Forge. If not, see <https://www.gnu.org/licenses/>.

import os

from setuptools import setup

VERSION = "0.1.0"

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
        "poyo",
        "pandas",
        "nexus-sdk",
        "aiohttp",
        "nest_asyncio"
    ],
    extras_require={
        "dev": ["pytest", "pytest-bdd", "pytest-cov", "pytest-mock"],
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
