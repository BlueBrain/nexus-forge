import re
from typing import Any, Dict, List, Match, Optional, Tuple, Union, Type, Pattern

from kgforge.core.commons.context import Context
from kgforge.core.commons.exceptions import QueryingError


# FIXME: need to find a comprehensive way (different than list) to get all SPARQL reserved clauses
SPARQL_CLAUSES = [
    "where",
    "filter",
    "select",
    "union",
    "limit",
    "construct",
    "optional",
    "bind",
    "values",
    "offset",
    "order by",
    "prefix",
    "graph",
    "distinct",
    "in",
    "as",
    "base",
    "prefix",
    "reduced",
    "describe",
    "ask",
    "named",
    "asc",
    "desc",
    "from",
    "optional",
    "graph",
    "regex",
    "union",
    "str",
    "lang",
    "langmatches",
    "datatype",
    "bound",
    "sameTerm",
    "isIRI",
    "isURI",
    "isBLANK",
    "isLITERAL",
    "group",
    "by",
    "order",
    "minus",
    "not",
    "exists"
]


def rewrite_sparql(query: str, context: Context, metadata_context: Context) -> str:
    """Rewrite local property and type names from Model.template() as IRIs.

    Local names are mapped to IRIs by using a JSON-LD context, i.e. { "@context": { ... }}
    from a kgforge.core.commons.Context.
    In the case of contexts using prefixed names, prefixes are added to the SPARQL query prologue.
    In the case of non-available contexts and vocab then the query is returned unchanged.
    """
    ctx = {}

    def _context_to_dict(c: Context):
        return {
            k: v["@id"] if isinstance(v, Dict) and "@id" in v else v
            for k, v in c.document["@context"].items()
        }
    if metadata_context and metadata_context.document:
        ctx.update(_context_to_dict(metadata_context))

    ctx.update(_context_to_dict(context))

    prefixes = context.prefixes
    has_prefixes = prefixes is not None and len(prefixes.keys()) > 0
    if ctx.get("type") == "@type":
        if "rdf" in prefixes:
            ctx["type"] = "rdf:type"
        else:
            ctx["type"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    def replace(match: Match) -> str:
        m4 = match.group(4)
        if m4 is None:
            return match.group(0)
        else:
            v = (
                ctx.get(m4, ":" + m4 if context.has_vocab() else None)
                if str(m4).lower() not in SPARQL_CLAUSES
                and not str(m4).startswith("https")
                else m4
            )
            if v is None:
                raise QueryingError(
                    f"Failed to construct a valid SPARQL query: add '{m4}'"
                    f", define an @vocab in the configured JSON-LD context or "
                    f"provide a fully correct SPARQL query."
                )
            m5 = match.group(5)
            if "//" in v:
                return f"<{v}>{m5}"
            else:
                return f"{v}{m5}"

    g4 = r"([a-zA-Z_]+)"
    g5 = r"([.;]?)"
    g0 = rf"((?<=[\s,[(/|!^])((a|true|false)|{g4}){g5}(?=[\s,\])/|?*+]))"
    g6 = r"(('[^']+')|('''[^\n\r]+''')|(\"[^\"]+\")|(\"\"\"[^\n\r]+\"\"\"))"
    rx = rf"{g0}|{g6}|(?<=< )(.*)(?= >)"
    qr = re.sub(rx, replace, query, flags=re.VERBOSE | re.MULTILINE)

    if not has_prefixes or "prefix" in str(qr).lower():
        return qr
    else:
        pfx = "\n".join(f"PREFIX {k}: <{v}>" for k, v in prefixes.items())
    if context.has_vocab():
        pfx = "\n".join([pfx, f"PREFIX : <{context.vocab}>"])
    return f"{pfx}\n{qr}"


def _replace_in_sparql(
        qr: str,
        what: str,
        value: Optional[int],
        default_value: int,
        search_regex: Pattern,
        replace_if_in_query=True
) -> str:

    is_what_in_query = bool(re.search(pattern=search_regex, string=qr))

    replace_value = f" {what} {value}" if value else \
        (f" {what} {default_value}" if default_value else None)

    if is_what_in_query:
        if not replace_if_in_query and value:
            raise QueryingError(
                f"Value for '{what}' is present in the provided query and set as argument: "
                f"set 'replace_if_in_query' to True to replace '{what}' when present in the query."
            )

        if replace_if_in_query and replace_value:
            qr = re.sub(pattern=search_regex, repl=replace_value, string=qr)
    else:
        if replace_value:
            qr = f"{qr} {replace_value}"  # Added to the end of the query (not very general)

    return qr


def handle_sparql_query(
        query: str, rewrite: bool,
        limit: Optional[int],
        offset: Optional[int],
        default_limit: int,
        default_offset: int,
        model_context: Context,
        metadata_context: Optional[Context],
        debug: bool
):
    qr = (
        rewrite_sparql(query, model_context, metadata_context)
        if model_context is not None and rewrite
        else query
    )
    if limit:
        qr = _replace_in_sparql(
            qr, "LIMIT", limit, default_limit,
            re.compile(r" LIMIT \d+", flags=re.IGNORECASE)
        )
    if offset:
        qr = _replace_in_sparql(
            qr, "OFFSET", offset, default_offset,
            re.compile(r" OFFSET \d+", flags=re.IGNORECASE)
        )

    if debug:
        _debug_query(qr)

    return qr


def _debug_query(query):
    if isinstance(query, Dict):
        print("Submitted query:", query)
    else:
        print(*["Submitted query:", *query.splitlines()], sep="\n   ")
