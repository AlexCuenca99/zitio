"""
This module defines the HTTP Content-Type constants and helpers.
"""

from werkzeug.http import parse_options_header

# Header name
CONTENT_TYPE = "Content-Type"

# Common media types
APPLICATION_JSON = "application/json"
APPLICATION_OCTET_STREAM = "application/octet-stream"
MULTIPART_FORM_DATA = "multipart/form-data"
TEXT_PLAIN = "text/plain"
APPLICATION_FORM_URLENCODED = "application/x-www-form-urlencoded"
APPLICATION_XML = "application/xml"


# Helper: vendor or +json types are common (ex: application/ld+json, application/vnd.foo+json)
def get_media_type(header_value: str) -> str:
    """Return the main media type (without parameters) from a Content-Type header."""
    if not header_value:
        return ""
    mimetype, options = parse_options_header(header_value)
    return mimetype or ""


def is_json(header_value: str) -> bool:
    """Detect JSON-like media types, including vendor types with +json."""
    mt = get_media_type(header_value).lower()
    return mt == APPLICATION_JSON or mt.endswith("+json")


def is_multipart(header_value: str) -> bool:
    """Return True for multipart/* content types (multipart/form-data, multipart/mixed, ...)."""
    mt = get_media_type(header_value).lower()
    return mt.startswith("multipart/")


def is_form_urlencoded(header_value: str) -> bool:
    """Detect application/x-www-form-urlencoded."""
    mt = get_media_type(header_value).lower()
    return mt == APPLICATION_FORM_URLENCODED
