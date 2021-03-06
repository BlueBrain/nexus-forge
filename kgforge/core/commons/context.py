#
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

from typing import Optional, Union, Dict, List

from rdflib_jsonld.context import Context as RdflibContext
from rdflib_jsonld.util import source_to_json


class Context(RdflibContext):
    """Context class will hold a JSON-LD context in two forms: iri and document.

    See also: https://w3c.github.io/json-ld-syntax/#the-context
    """

    def __init__(self, document: Union[Dict, List, str], iri: Optional[str] = None) -> None:
        """Initialize the Context and resolves the document if necessary.

        The document can be provided as a dictionary, list or string. If a dictionary or list is
        provided, we assume that nothing needs to be resolved. If a string is provided,
        it should correspond to a resolvable document (i.e. file://, http://) which will be
        resolved in the initialization, the result will become the document and the iri will
        be the initial document parameter. Will throw an exception if the context is not resolvable.

        Args:
            document (Dict, List, str): resolved or resolvable document
            iri (str): the iri for the provided document
        """
        super().__init__(document)
        if isinstance(document, list):
            sub_docs = dict()
            for x in document:
                sub_context = Context(x)
                sub_docs.update(sub_context.document["@context"])
            self.document = {"@context": sub_docs}
        elif isinstance(document, str):
            try:
                self.document = source_to_json(document)
            except Exception:
                raise ValueError("context not resolvable")
        elif isinstance(document, Dict):
            self.document = document if "@context" in document else {"@context": document}
        self.iri = iri
        self.prefixes = {v: k for k, v in self._prefixes.items() if k.endswith(("/", "#"))}

    def is_http_iri(self):
        if self.iri:
            return self.iri.startswith("http")
        else:
            return False

    def has_vocab(self):
        return self.vocab is not None
