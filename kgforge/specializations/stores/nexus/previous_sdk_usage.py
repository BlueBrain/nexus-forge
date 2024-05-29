import puremagic
import json
import collections
import requests
from typing import Any, Dict, List, Optional, Tuple, Union, Type
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

SEGMENT = "files"
DEFAULT_MIME = "application/octet-stream"

# to make sure the output response dictionary are always ordered like the response's json
decode_json_ordered = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode

# defines some parts of the header, to combine together
header_parts = {
    "common": {"mode": "cors"},
    "json": {"Content-Type": "application/json"},
    "text": {"sendAs": "text", "Content-Type": "text/plain"},
    "sparql": {"Content-Type": "application/sparql-query"},
    "file": {},
}

# so that a get request can decide to retrieve JSON or binary
header_accept = {
    "json": "application/ld+json, application/json",
    "all": "*/*"
}

default_type = "json"
header_parts["default"] = header_parts[default_type]


def _content_type(filepath: str, content_type: Optional[str]) -> str:
    if content_type is None:
        try:
            guessed_content_type = puremagic.from_file(filepath, True)
        except puremagic.main.PureError as e:
            print(e)
            print("using the default content type instead:", DEFAULT_MIME)
            guessed_content_type = DEFAULT_MIME
        return guessed_content_type
    else:
        return content_type


def files_create(
        endpoint: Optional[str],
        token: Optional[str],
        org_label: str, project_label: str, filepath: str, storage_id: Optional[str] = None,
        file_id: Optional[str] = None, filename: Optional[str] = None, content_type: Optional[str] = None
) -> Dict:
    """
        Creates a file resource from a binary attachment using the POST method when the user does not provide
        a file ID, PUT otherwise.

        :param endpoint: the endpoint base, mandatory is use_base is True, else it is not used
        :param token: the authentication token
        :param org_label: The label of the organization that the file belongs to
        :param project_label: The label of the project that the file belongs to
        :param filepath: path of the file to upload
        :param storage_id: OPTIONAL The id of the storage backend where the file will be stored.
                           If not provided, the project's default storage is used.
        :param file_id: OPTIONAL Will use this id to identify the file if provided.
                        If not provided, an ID will be generated.
        :param filename: OPTIONAL Overrides the automatically detected filename
        :param content_type: OPTIONAL Override the automatically detected content type
        :return: A payload containing only the Nexus metadata for this updated file.
    """

    # the elements composing the query URL need to be URL-encoded
    org_label = quote_plus(org_label)
    project_label = quote_plus(project_label)

    path = [SEGMENT, org_label, project_label]

    if filename is None:
        filename = filepath.split("/")[-1]

    file_obj = {
        "file": (filename, open(filepath, "rb"), _content_type(filepath, content_type))
    }

    if file_id is None:
        return http_post(environment=endpoint, token=token, path=path, body=file_obj, data_type="file", storage=storage_id)
    else:
        path.append(quote_plus(file_id))
        return http_put(environment=endpoint, token=token, path=path, body=file_obj, data_type="file", storage=storage_id)


# TODO add docstring
def http_post(environment: Optional[str], token: Optional[str], path: Union[str, List[str]], body=None, data_type="default", use_base=False, **kwargs):
    """
        Perform a POST request.
        :param environment: the endpoint base, mandatory is use_base is True, else it is not used
        :param token: the authentication token
        :param path: complete URL if use_base is False or just the ending if use_base is True
        :param body: OPTIONAL Things to send, can be a dictionary
        :param data_type: OPTIONAL can be "json" or "text" (default: "default" = "json")
        :param params: OPTIONAL provide some URL parameters (?foo=bar&hello=world) as a dictionary
        :return: the dictionary that is equivalent to the json response
    """
    header = prepare_header(token=token, type=data_type)
    full_url = _full_url(environment, path, use_base)

    if data_type != "file":
        body_data = prepare_body(body, data_type)
        response = requests.post(full_url, headers=header, data=body_data, params=kwargs)
    else:
        response = requests.post(full_url, headers=header, files=body, params=kwargs)

    response.raise_for_status()
    return decode_json_ordered(response.text)


def http_put(environment: Optional[str], token: Optional[str], path: Union[str, List[str]], body=None, data_type="default", use_base=False, **kwargs):
    """
        Performs a PUT request

        :param path: complete URL if use_base si False or just the ending if use_base is True
        :param body: OPTIONAL Things to send, can be a dictionary or a buffer
        :param data_type: OPTIONAL can be "json" or "text" or "file" (default: "default" = "json")
        :param use_base: OPTIONAL if True, the Nexus env provided by nexus.config.set_environment will
        be prepended to path. (default: False)

        :param params: OPTIONAL provide some URL parameters (?foo=bar&hello=world) as a dictionary
        :return: the dictionary that is equivalent to the json response
    """
    header = prepare_header(token=token, type=data_type)
    full_url = _full_url(environment, path, use_base)

    if data_type != "file":
        body_data = prepare_body(body, data_type)
        response = requests.put(full_url, headers=header, data=body_data, params=kwargs)
    else:
        response = requests.put(full_url, headers=header, files=body, params=kwargs)

    response.raise_for_status()
    return decode_json_ordered(response.text)


def prepare_header(token: Optional[str], type="default", accept="json"):
    """
        Prepare the header of the HTTP request by fetching the token from the config
        and few other things.

        :param type: string. Must be one of the keys in the above declared dict header_parts
        :param accept: OPTIONAL if "json", the answer will be JSON, if "all" it will be something else if the
                       request can send something else (e.g. binary)

    """
    header = {**header_parts["common"], **header_parts[type]}

    if accept in header_accept:
        header["Accept"] = header_accept[accept]

    if token:
        header["Authorization"] = "Bearer " + token

    return header


# Internal helpers
def _full_url(environment: str, path: Union[str, List[str]], use_base: bool) -> str:
    # 'use_base' is temporary for compatibility with previous code sections.
    if use_base:
        return environment + path

    if isinstance(path, str):
        return path
    elif isinstance(path, list):
        url = [environment] + path
        return "/".join(url)
    else:
        raise TypeError("Expecting a string or a list!")


def prepare_body(data, type="default"):
    """
        Prepare the body of the HTTP request

        :param data:
        :param type:
        :return:
    """
    if type == "default":
        type = default_type

    if type == "json":
        body = json.dumps(data, ensure_ascii=True)
    else:
        body = data

    if data is None:
        body = None

    return body
